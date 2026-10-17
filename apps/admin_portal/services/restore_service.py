"""Restore trusted server backups after a verified recovery snapshot."""

import json
import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from django.conf import settings

from apps.accounts.permissions import require_active_admin
from .backup_service import create_database_backup, get_backup_dir, get_database_config, verify_database_backup
from .maintenance import database_access, recovery_marker_path


logger = logging.getLogger(__name__)


class RestoreFailed(RuntimeError):
    """Import may have changed the database; maintenance must remain enabled."""


def validate_backup_filename(filename: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.sql", filename or "") or ".." in filename:
        raise ValueError("Invalid backup filename. Select a server-created .sql backup.")
    backup_dir = get_backup_dir().resolve()
    target_path = (backup_dir / filename).resolve()
    if not target_path.is_relative_to(backup_dir):
        raise ValueError("Backup path is outside the backups directory.")
    if not target_path.is_file():
        raise ValueError("The selected backup file was not found.")
    return target_path


def restore_confirmation(filename, database_name):
    return f"RESTORE {filename} TO {database_name}"


def restore_database_from_backup(filename: str, confirmation: str, *, actor,
                                 target_database: str, maintenance_ack: bool) -> Path:
    """Return the retained recovery snapshot; never claim an import rollback.

    HTTP workers must share this checkout's lock directory. The operator must
    also stop scheduled jobs, management commands and direct MySQL writers.
    """
    admin = require_active_admin(actor)
    config = get_database_config()
    database_name = config["NAME"]
    file_path = validate_backup_filename(filename)
    if (target_database != database_name
            or confirmation != restore_confirmation(filename, database_name)):
        raise ValueError("Confirm the exact backup filename and target database before restoring.")
    if not maintenance_ack:
        raise ValueError("Confirm the maintenance window and pause all external database writers before restoring.")
    verify_database_backup(file_path)

    bin_dir = os.getenv("MYSQL_BIN")
    executable = (Path(bin_dir) / "mysql.exe") if bin_dir else shutil.which("mysql")
    if not executable or not Path(executable).is_file():
        raise RuntimeError("mysql executable is unavailable on the system.")
    middleware = "apps.admin_portal.services.maintenance.DatabaseMaintenanceMiddleware"
    if not settings.MIDDLEWARE or settings.MIDDLEWARE[0] != middleware:
        raise RuntimeError("Database maintenance middleware must be enabled before restoring.")

    with database_access(exclusive=True):
        admin = require_active_admin(admin)
        started = time.monotonic()
        logger.info("database_restore start actor_id=%s database=%s source=%s", admin.pk, database_name, filename)
        try:
            recovery_path = create_database_backup(actor_id=admin.pk, purpose="pre_restore")
            verify_database_backup(recovery_path)
        except (OSError, ValueError, RuntimeError):
            logger.error("database_restore stopped actor_id=%s database=%s source=%s reason=pre_backup_failed duration_s=%.3f",
                         admin.pk, database_name, filename, time.monotonic() - started)
            raise RuntimeError("Pre-restore backup failed verification. Restore was not started; the current database was not replaced.") from None

        verify_database_backup(file_path)
        marker = recovery_marker_path()
        with file_path.open("rb") as input_file:
            with marker.open("x", encoding="utf-8") as state:
                json.dump({"database": database_name, "source": filename,
                           "recovery_backup": recovery_path.name, "actor_id": admin.pk,
                           "state": "recovery_required"}, state)
            environment = os.environ.copy()
            environment["MYSQL_PWD"] = config.get("PASSWORD", "") or ""
            argv = [str(executable), "--default-character-set=utf8mb4",
                    f"--host={config.get('HOST') or '127.0.0.1'}",
                    f"--port={config.get('PORT') or '3306'}",
                    f"--user={config['USER']}", database_name]
            try:
                result = subprocess.run(argv, stdin=input_file, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.PIPE, env=environment,
                                        timeout=300, check=False, shell=False)
                if result.returncode != 0:
                    raise RestoreFailed(f"mysql exited with code {result.returncode}")
            except (subprocess.TimeoutExpired, OSError, RestoreFailed) as exc:
                logger.error("database_restore failure actor_id=%s database=%s source=%s recovery=%s reason=%s duration_s=%.3f",
                             admin.pk, database_name, filename, recovery_path.name, type(exc).__name__, time.monotonic() - started)
                raise RestoreFailed(
                    f"Restore failed or timed out and may have applied partially. Recovery backup retained: {recovery_path.name}. "
                    "Database access remains blocked. Keep external writers stopped; ask the operator to verify/import this "
                    "recovery backup under maintenance, validate the database, then remove database/backups/.restore-recovery.json "
                    "before reopening access. MySQL restore was not rolled back."
                ) from None
            finally:
                environment.pop("MYSQL_PWD", None)

        marker.unlink()
        logger.info("database_restore success actor_id=%s database=%s source=%s recovery=%s duration_s=%.3f",
                    admin.pk, database_name, filename, recovery_path.name, time.monotonic() - started)
        return recovery_path
