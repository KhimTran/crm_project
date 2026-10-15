"""Database restore service for MySQL crm_db."""

import os
import re
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from apps.admin_portal.services.backup_service import get_backup_dir


def validate_backup_filename(filename: str) -> Path:
    if not filename or not filename.endswith(".sql"):
        raise ValueError("Invalid backup filename. Must be a .sql file.")
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("Directory traversal is not allowed in filename.")

    backup_dir = get_backup_dir()
    target_path = (backup_dir / filename).resolve()
    if not target_path.is_relative_to(backup_dir.resolve()):
        raise ValueError("Security violation: path is outside the backups directory.")
    if not target_path.is_file():
        raise FileNotFoundError(f"Backup file '{filename}' was not found.")
    return target_path


def restore_database_from_backup(filename: str, confirmation: str) -> None:
    if confirmation.strip().upper() != "RESTORE":
        raise ValueError("You must type 'RESTORE' exactly to confirm database restoration.")

    file_path = validate_backup_filename(filename)

    config = settings.DATABASES["default"]
    if config["ENGINE"] != "django.db.backends.mysql":
        raise RuntimeError("Database restore requires a MySQL database backend.")

    bin_dir = os.getenv("MYSQL_BIN")
    executable = (Path(bin_dir) / "mysql.exe") if bin_dir else shutil.which("mysql")
    if not executable or not Path(executable).is_file():
        raise RuntimeError("mysql executable is unavailable on the system.")

    data = file_path.read_bytes()
    if len(data) < 100:
        raise ValueError("Selected backup file is empty or corrupted.")

    if re.search(rb"(?im)^\s*(CREATE|DROP)\s+DATABASE\b|^\s*USE\s+", data):
        raise ValueError("Backup file contains unsafe CREATE/DROP DATABASE or USE statements.")

    environment = os.environ.copy()
    environment["MYSQL_PWD"] = config.get("PASSWORD", "") or ""

    host = config.get("HOST", "127.0.0.1") or "127.0.0.1"
    port = str(config.get("PORT", "3306") or "3306")
    user = config.get("USER", "root") or "root"
    db_name = config["NAME"]

    argv = [
        str(executable),
        "--default-character-set=utf8mb4",
        f"--host={host}",
        f"--port={port}",
        f"--user={user}",
        db_name,
    ]

    try:
        with file_path.open("rb") as input_file:
            result = subprocess.run(
                argv,
                stdin=input_file,
                stderr=subprocess.PIPE,
                env=environment,
                timeout=300,
                check=False,
            )
        if result.returncode != 0:
            err_msg = result.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"mysql restore failed (code {result.returncode}): {err_msg}")
    finally:
        environment.pop("MYSQL_PWD", None)
