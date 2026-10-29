"""Database backup service for MySQL crm_db."""

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from django.conf import settings


logger = logging.getLogger(__name__)


def get_database_config():
    config = settings.DATABASES["default"]
    if config["ENGINE"] != "django.db.backends.mysql":
        raise RuntimeError("Database tools require a MySQL database backend.")
    if not re.fullmatch(r"[A-Za-z0-9_]+", config.get("NAME") or "") or not config.get("USER"):
        raise ValueError("Database name and user must be configured for database tools.")
    return config


def get_backup_dir() -> Path:
    backup_dir = Path(settings.BASE_DIR) / "database" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def _inspect_dump(path):
    """Check trusted mysqldump output completeness and compute its digest.

    This checks integrity, not the safety of arbitrary uploaded SQL. The backup
    directory and manifests are server controlled and must not accept uploads.
    """
    size = path.stat().st_size
    if size < 100:
        raise ValueError("Backup file is empty or incomplete.")
    digest = hashlib.sha256()
    has_table = False
    previous = b""
    with path.open("rb") as stream:
        header = stream.read(1024)
        if not header.startswith(b"-- MySQL dump"):
            raise ValueError("Backup is not trusted MySQL dump output.")
        stream.seek(0)
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            block = previous + chunk
            if re.search(rb"(?im)^\s*(CREATE|DROP)\s+DATABASE\b|^\s*USE\s+", block):
                raise ValueError("Backup contains database-selection statements.")
            has_table = has_table or b"CREATE TABLE " in block
            previous = block[-1024:]
        if not has_table or b"-- Dump completed on " not in previous:
            raise ValueError("Backup is missing its schema or completion marker.")
    return size, digest.hexdigest()


def verify_database_backup(path: Path):
    """Re-read the published file and its manifest; fail closed on corruption."""
    size, checksum = _inspect_dump(path)
    try:
        manifest = json.loads(path.with_suffix(".sql.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError("Backup has no valid verification manifest. Create a new system backup.") from None
    if (not isinstance(manifest, dict) or manifest.get("version") != 1 or manifest.get("size_bytes") != size
            or manifest.get("sha256") != checksum):
        raise ValueError("Backup verification failed. The file may be incomplete or changed.")
    return manifest


def create_database_backup(*, actor_id=None, purpose="manual") -> Path:
    config = get_database_config()

    bin_dir = os.getenv("MYSQL_BIN") or getattr(settings, "MYSQL_BIN", None)
    executable = None
    if bin_dir:
        clean_bin = Path(str(bin_dir).strip("'\""))
        candidate = clean_bin / "mysqldump.exe"
        if candidate.is_file():
            executable = candidate
        elif (clean_bin / "mysqldump").is_file():
            executable = clean_bin / "mysqldump"
    if not executable:
        executable = shutil.which("mysqldump")
    if not executable or not Path(executable).is_file():
        raise RuntimeError("mysqldump executable is unavailable on the system.")

    directory = get_backup_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid4().hex[:8]
    filename = f"{config['NAME']}_{timestamp}_{unique_suffix}.sql"
    final_path = directory / filename
    temporary_path = directory / f"{filename}.partial"
    manifest_path = final_path.with_suffix(".sql.json")

    environment = os.environ.copy()
    environment["MYSQL_PWD"] = config.get("PASSWORD", "") or ""

    host = config.get("HOST", "127.0.0.1") or "127.0.0.1"
    port = str(config.get("PORT", "3306") or "3306")
    user = config.get("USER", "root") or "root"
    db_name = config["NAME"]

    argv = [
        str(executable),
        "--single-transaction",
        "--quick",
        "--no-tablespaces",
        "--default-character-set=utf8mb4",
        "--set-gtid-purged=OFF",
        "--routines",
        "--events",
        "--triggers",
        f"--host={host}",
        f"--port={port}",
        f"--user={user}",
        db_name,
    ]

    started = time.monotonic()
    logger.info("database_backup start actor_id=%s database=%s purpose=%s", actor_id, db_name, purpose)
    published = False
    try:
        with temporary_path.open("wb") as output:
            result = subprocess.run(
                argv,
                stdout=output,
                stderr=subprocess.PIPE,
                env=environment,
                timeout=300,
                check=False,
                shell=False,
            )
        if result.returncode != 0:
            raise RuntimeError(f"mysqldump failed (exit code {result.returncode}). Check database tool configuration and permissions.")

        size, checksum = _inspect_dump(temporary_path)

        temporary_path.replace(final_path)
        manifest_path.write_text(json.dumps({
            "version": 1, "database": db_name, "size_bytes": size,
            "sha256": checksum, "created_at": datetime.now(timezone.utc).isoformat(),
        }), encoding="utf-8")
        verify_database_backup(final_path)
        published = True
        logger.info("database_backup success actor_id=%s database=%s filename=%s sha256=%s purpose=%s duration_s=%.3f",
                    actor_id, db_name, filename, checksum, purpose, time.monotonic() - started)
        return final_path
    except subprocess.TimeoutExpired:
        logger.error("database_backup failure actor_id=%s database=%s reason=timeout purpose=%s duration_s=%.3f",
                     actor_id, db_name, purpose, time.monotonic() - started)
        raise RuntimeError("Database backup timed out; no verified backup was published.") from None
    except (OSError, ValueError, RuntimeError) as exc:
        logger.error("database_backup failure actor_id=%s database=%s reason=%s purpose=%s duration_s=%.3f",
                     actor_id, db_name, type(exc).__name__, purpose, time.monotonic() - started)
        raise RuntimeError("Database backup failed; no verified backup was published. Check database tool configuration, permissions and disk space.") from None
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
        if not published:
            final_path.unlink(missing_ok=True)
            manifest_path.unlink(missing_ok=True)
        environment.pop("MYSQL_PWD", None)


def list_database_backups() -> list[dict]:
    directory = get_backup_dir()
    backups = []
    for file_path in directory.glob("*.sql"):
        if file_path.is_file() and file_path.resolve().is_relative_to(directory.resolve()):
            try:
                verify_database_backup(file_path)
                verified = True
            except (OSError, ValueError):
                verified = False
            stat = file_path.stat()
            size_bytes = stat.st_size
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"

            mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            backups.append({
                "filename": file_path.name,
                "size_bytes": size_bytes,
                "size_display": size_str,
                "created_at": mtime,
                "path": str(file_path),
                "verified": verified,
            })
    backups.sort(key=lambda b: b["created_at"], reverse=True)
    return backups
