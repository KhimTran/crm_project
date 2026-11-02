"""Restore trusted server backups after a verified recovery snapshot."""

import json
import logging
import os
import re
import shutil
import subprocess
import time
import hashlib
from uuid import uuid4
from contextlib import contextmanager
from django.db import connection
from pathlib import Path

from django.conf import settings

from apps.accounts.permissions import require_active_admin
from .backup_service import create_database_backup, get_backup_dir, get_database_config, verify_database_backup
from .maintenance import database_access, recovery_marker_path


logger = logging.getLogger(__name__)


def database_fingerprint(client):
    """Compare all table columns and row values, independent of row order."""
    cursor = client.cursor()
    try:
        cursor.execute('SHOW TABLES')
        tables = [row[0] for row in cursor.fetchall()]
        result = {}
        for table in tables:
            quoted = '`' + table.replace('`', '``') + '`'
            cursor.execute('SELECT * FROM ' + quoted)
            columns = [item[0] for item in cursor.description]
            rows = sorted(repr(tuple(row)) for row in cursor.fetchall())
            result[table] = (columns, len(rows), hashlib.sha256('\n'.join(rows).encode()).hexdigest())
        return result
    finally:
        cursor.close()


@contextmanager
def verified_import_snapshot(file_path, executable, argv, environment):
    """Reject broken SQL before touching the target; inspect its real contents."""
    name = 'crm_restore_verify_' + uuid4().hex[:16]
    params = connection.get_connection_params()
    params.pop('database', None)
    client = connection.Database.connect(**params)
    cursor = client.cursor()
    created = False
    try:
        cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        created = True
        with file_path.open('rb') as source:
            result = subprocess.run([*argv[:-1], name], stdin=source, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.PIPE, env=environment, timeout=300, check=False)
        if result.returncode:
            # Keep raw stderr private; log the MySQL error code and SQL line only.
            detail = re.search(rb'ERROR\s+\d+.*?at line\s+\d+', result.stderr or b'')
            logger.error('database_restore preflight_sql_failed detail=%s', detail.group().decode(errors='replace') if detail else 'mysql_error')
            raise ValueError('Backup SQL could not be imported into the verification database. The current database was not changed.')
        cursor.execute(f'USE `{name}`')
        snapshot = database_fingerprint(client)
        if not snapshot or not any(value[1] for value in snapshot.values()):
            raise ValueError('The backup has no data. Select a full schema and data backup.')
        yield snapshot
    finally:
        if created:
            cursor.execute(f'DROP DATABASE `{name}`')
        cursor.close()
        client.close()


class RestoreFailed(RuntimeError):
    """Import may have changed the database; maintenance must remain enabled."""


class RestoreRecovered(RestoreFailed):
    """Requested restore failed, but the pre-request state was recovered and verified."""


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

    bin_dir = os.getenv("MYSQL_BIN") or getattr(settings, "MYSQL_BIN", None)
    executable = None
    if bin_dir:
        clean_bin = Path(str(bin_dir).strip("'\""))
        candidate = clean_bin / "mysql.exe"
        if candidate.is_file():
            executable = candidate
        elif (clean_bin / "mysql").is_file():
            executable = clean_bin / "mysql"
    else:
        executable = shutil.which("mysql")
    if not executable or not Path(executable).is_file():
        raise RuntimeError("mysql executable is unavailable on the system.")
    middleware = "apps.admin_portal.services.maintenance.DatabaseMaintenanceMiddleware"
    if not settings.MIDDLEWARE or settings.MIDDLEWARE[0] != middleware:
        raise RuntimeError("Database maintenance middleware must be enabled before restoring.")

    with database_access(exclusive=True):
        admin = require_active_admin(admin)
        started = time.monotonic()
        connection.ensure_connection()
        before_restore = database_fingerprint(connection.connection)
        logger.info("database_restore start actor_id=%s database=%s source=%s", admin.pk, database_name, filename)
        try:
            recovery_path = create_database_backup(actor_id=admin.pk, purpose="pre_restore")
            verify_database_backup(recovery_path)
        except (OSError, ValueError, RuntimeError):
            logger.error("RESTORE_FAILED actor_id=%s database=%s source=%s reason=pre_backup_failed target_unchanged=true duration_s=%.3f",
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
                with verified_import_snapshot(file_path, executable, argv, environment) as expected:
                    result = subprocess.run(argv, stdin=input_file, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.PIPE, env=environment,
                                            timeout=300, check=False, shell=False)
                    if result.returncode != 0:
                        detail = re.search(rb'ERROR\s+(\d+).*?at line\s+(\d+)', result.stderr or b'')
                        reason = f' error={detail[1].decode()} sql_line={detail[2].decode()}' if detail else ''
                        raise RestoreFailed(f"mysql exited with code {result.returncode}{reason}")
                    connection.close()
                    connection.ensure_connection()
                    if database_fingerprint(connection.connection) != expected:
                        raise RestoreFailed('Restored table data did not match the selected backup')
            except ValueError:
                logger.error('RESTORE_FAILED actor_id=%s database=%s source=%s reason=preflight_rejected target_unchanged=true', admin.pk, database_name, filename)
                marker.unlink(missing_ok=True)
                raise
            except (subprocess.TimeoutExpired, OSError, RestoreFailed, connection.Database.Error) as exc:
                logger.error("RESTORE_FAILED actor_id=%s database=%s source=%s recovery=%s reason=%s duration_s=%.3f",
                             admin.pk, database_name, filename, recovery_path.name, str(exc) if isinstance(exc, RestoreFailed) else type(exc).__name__, time.monotonic() - started)
                logger.info('RECOVERY_STARTED actor_id=%s database=%s source=%s recovery=%s', admin.pk, database_name, filename, recovery_path.name)
                try:
                    verify_database_backup(recovery_path)
                    with recovery_path.open('rb') as recovery_file:
                        recovered = subprocess.run(argv, stdin=recovery_file, stdout=subprocess.DEVNULL,
                                                   stderr=subprocess.PIPE, env=environment,
                                                   timeout=300, check=False, shell=False)
                    if recovered.returncode:
                        raise RestoreFailed(f'mysql recovery exited with code {recovered.returncode}')
                    connection.close()
                    connection.ensure_connection()
                    if database_fingerprint(connection.connection) != before_restore:
                        raise RestoreFailed('Recovery data did not match the pre-restore state')
                    marker.unlink()
                except (ValueError, OSError, subprocess.TimeoutExpired, RestoreFailed, connection.Database.Error) as recovery_error:
                    logger.error('RECOVERY_FAILED actor_id=%s database=%s source=%s recovery=%s reason=%s',
                                 admin.pk, database_name, filename, recovery_path.name,
                                 str(recovery_error) if isinstance(recovery_error, (RestoreFailed, ValueError)) else type(recovery_error).__name__)
                    raise RestoreFailed(f'Restore and automatic recovery failed. Access remains blocked. Recovery backup: {recovery_path.name}. Operator recovery and verification are required.') from None
                logger.info('RECOVERY_SUCCESS actor_id=%s database=%s source=%s recovery=%s verified=true', admin.pk, database_name, filename, recovery_path.name)
                raise RestoreRecovered('Restore failed. The previous database was automatically recovered and verified. No requested restore was applied.') from None
            finally:
                environment.pop("MYSQL_PWD", None)

        marker.unlink()
        logger.info("RESTORE_SUCCESS actor_id=%s database=%s source=%s recovery=%s verified=true duration_s=%.3f",
                    admin.pk, database_name, filename, recovery_path.name, time.monotonic() - started)
        return recovery_path
