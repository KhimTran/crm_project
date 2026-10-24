"""Restore a verified crm_db dump into an unused disposable DB and migrate it.

Requires explicit confirmation of the exact backup and target before invocation.
Never drops an existing database and never changes crm_db.
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()
from django.conf import settings  # noqa: E402
from django.db import connection  # noqa: E402
import MySQLdb  # noqa: E402


BUSINESS_TABLES = (
    "accounts", "customers", "categories", "brands", "products",
    "customer_preferences", "feedbacks", "surveys", "survey_questions",
    "survey_options", "survey_recipients", "survey_responses", "survey_answers",
)
TARGET = "crm_db_import_test"


def counts(cursor, tables):
    result = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        result[table] = cursor.fetchone()[0]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("backup_name")
    parser.add_argument("sha256")
    parser.add_argument("target")
    args = parser.parse_args()
    if args.target != TARGET or not re.fullmatch(r"crm_db_\d{8}_\d{6}_[0-9a-f]{8}\.sql", args.backup_name):
        raise RuntimeError("Only a generated backup and crm_db_import_test are allowed")
    backup_root = (ROOT / "database" / "backups").resolve()
    backup = (backup_root / args.backup_name).resolve()
    if backup.parent != backup_root or not backup.is_file():
        raise RuntimeError("Backup path is invalid")
    data = backup.read_bytes()
    if len(data) < 1024 or hashlib.sha256(data).hexdigest() != args.sha256:
        raise RuntimeError("Backup integrity check failed")
    if re.search(rb"(?im)^\s*(CREATE|DROP)\s+DATABASE\b|^\s*USE\s+`?crm_db`?\s*;", data):
        raise RuntimeError("Backup selects or modifies a database by name")
    config = settings.DATABASES["default"]
    if config["NAME"] != "crm_db":
        raise RuntimeError("Source must be crm_db")
    with connection.cursor() as cursor:
        cursor.execute("SHOW DATABASES LIKE %s", [TARGET])
        if cursor.fetchone():
            raise RuntimeError(f"Target {TARGET} already exists; refusing to overwrite it")
        before = counts(cursor, BUSINESS_TABLES + ("django_session",))
        cursor.execute("SELECT account_id, password_hash FROM accounts ORDER BY account_id")
        account_rows = cursor.fetchall()
    mysql_bin = os.getenv("MYSQL_BIN")
    executable = (Path(mysql_bin) / "mysql.exe") if mysql_bin else shutil.which("mysql")
    if not executable or not Path(executable).is_file():
        raise RuntimeError("mysql client is unavailable")
    environment = os.environ.copy()
    environment["MYSQL_PWD"] = config["PASSWORD"] or ""

    # The target is explicitly named and verified absent. No DROP is issued.
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE `{TARGET}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    try:
        with backup.open("rb") as input_file:
            imported = subprocess.run(
                [str(executable), f"--host={config['HOST']}", f"--port={config['PORT']}",
                 f"--user={config['USER']}", TARGET],
                stdin=input_file, stderr=subprocess.PIPE, env=environment,
                timeout=300, check=False,
            )
        if imported.returncode:
            raise RuntimeError(f"Restore failed with exit code {imported.returncode}; target retained for inspection")
        migrate_env = os.environ.copy()
        migrate_env["DB_NAME"] = TARGET
        migrated = subprocess.run(
            [sys.executable, str(ROOT / "manage.py"), "migrate", "--noinput"],
            env=migrate_env, cwd=ROOT, timeout=300, check=False,
        )
        if migrated.returncode:
            raise RuntimeError(f"Migration rehearsal failed with exit code {migrated.returncode}; target retained")
        target_connection = MySQLdb.connect(
            host=config["HOST"], port=int(config["PORT"]), user=config["USER"],
            passwd=config["PASSWORD"], db=TARGET, charset="utf8mb4",
        )
        try:
            cursor = target_connection.cursor()
            after = counts(cursor, BUSINESS_TABLES + ("django_session",))
            if before != after:
                raise RuntimeError(f"Row counts changed: {before} -> {after}")
            cursor.execute("SELECT account_id, password_hash FROM accounts ORDER BY account_id")
            if cursor.fetchall() != account_rows:
                raise RuntimeError("Account IDs or password hashes changed")
            cursor.execute(
                "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = %s AND (COLUMN_NAME = 'id' OR COLUMN_NAME LIKE '%%_id' "
                "OR COLUMN_NAME IN ('created_by', 'handled_by'))", [TARGET]
            )
            bad = [(table, column, kind) for table, column, kind in cursor.fetchall()
                   if (table, column) != ("django_admin_log", "object_id") and kind != "int"]
            if bad:
                raise RuntimeError(f"Non-INT IDs remain: {bad}")
            cursor.execute(
                "SELECT TABLE_NAME, CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS "
                "WHERE TABLE_SCHEMA = %s", [TARGET]
            )
            constraints = set(cursor.fetchall())
            for constraint in (("suppliers", "uq_suppliers_code"),
                               ("survey_recipients", "uq_survey_recipients_survey_customer"),
                               ("survey_responses", "uq_survey_responses_recipient")):
                if constraint not in constraints:
                    raise RuntimeError(f"Constraint missing: {constraint}")
            cursor.execute(
                "SELECT UPDATE_RULE, DELETE_RULE FROM information_schema.REFERENTIAL_CONSTRAINTS "
                "WHERE CONSTRAINT_SCHEMA = %s AND TABLE_NAME = 'products' "
                "AND CONSTRAINT_NAME = 'fk_products_supplier'", [TARGET]
            )
            if cursor.fetchone() != ("CASCADE", "RESTRICT"):
                raise RuntimeError("Supplier FK rules changed")
        finally:
            target_connection.close()
    finally:
        environment.pop("MYSQL_PWD", None)
    print(f"Restore and migration verified on {TARGET}; {len(before)} source table counts preserved")


if __name__ == "__main__":
    main()
