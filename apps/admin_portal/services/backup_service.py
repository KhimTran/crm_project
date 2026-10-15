"""Database backup service for MySQL crm_db."""

import hashlib
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from django.conf import settings


def get_backup_dir() -> Path:
    backup_dir = Path(settings.BASE_DIR) / "database" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def create_database_backup() -> Path:
    config = settings.DATABASES["default"]
    if config["ENGINE"] != "django.db.backends.mysql":
        raise RuntimeError("Database backup requires a MySQL database backend.")

    bin_dir = os.getenv("MYSQL_BIN")
    executable = (Path(bin_dir) / "mysqldump.exe") if bin_dir else shutil.which("mysqldump")
    if not executable or not Path(executable).is_file():
        raise RuntimeError("mysqldump executable is unavailable on the system.")

    directory = get_backup_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid4().hex[:8]
    filename = f"{config['NAME']}_{timestamp}_{unique_suffix}.sql"
    final_path = directory / filename
    temporary_path = directory / f"{filename}.partial"

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

    try:
        with temporary_path.open("wb") as output:
            result = subprocess.run(
                argv,
                stdout=output,
                stderr=subprocess.PIPE,
                env=environment,
                timeout=300,
                check=False,
            )
        if result.returncode != 0:
            err_msg = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"mysqldump failed (code {result.returncode}): {err_msg}")

        data = temporary_path.read_bytes()
        if len(data) < 100:
            raise RuntimeError("Generated backup file is too small or empty.")

        temporary_path.replace(final_path)
        return final_path
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
        environment.pop("MYSQL_PWD", None)


def list_database_backups() -> list[dict]:
    directory = get_backup_dir()
    backups = []
    for file_path in directory.glob("*.sql"):
        if file_path.is_file():
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
            })
    backups.sort(key=lambda b: b["created_at"], reverse=True)
    return backups
