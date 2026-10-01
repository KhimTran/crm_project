"""Export the migrated and seeded crm_db, including Django technical tables."""

import hashlib
import os
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


def main():
    config = settings.DATABASES["default"]
    if config["ENGINE"] != "django.db.backends.mysql" or config["NAME"] != "crm_db":
        raise RuntimeError("Export source must be MySQL crm_db")
    with connection.cursor() as cursor:
        cursor.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE'")
        tables = {row[0] for row in cursor.fetchall()}
        if len(tables) != 23 or not {"django_migrations", "django_session", "accounts", "suppliers", "survey_answers"}.issubset(tables):
            raise RuntimeError("Migrated database does not contain the expected 23 tables")
        cursor.execute("SELECT COUNT(*) FROM django_migrations")
        if cursor.fetchone()[0] != 24:
            raise RuntimeError("Expected all 24 migrations before export")
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        if cursor.fetchone()[0] < 8:
            raise RuntimeError("Expected at least eight demo suppliers before export")
    bin_dir = os.getenv("MYSQL_BIN")
    executable = (Path(bin_dir) / "mysqldump.exe") if bin_dir else shutil.which("mysqldump")
    if not executable or not Path(executable).is_file():
        raise RuntimeError("mysqldump is unavailable")
    output_path = ROOT / "database" / "crm_db.sql"
    temporary_path = output_path.with_suffix(".sql.partial")
    environment = os.environ.copy()
    environment["MYSQL_PWD"] = config["PASSWORD"] or ""
    argv = [str(executable), "--single-transaction", "--quick", "--no-tablespaces",
            "--default-character-set=utf8mb4", "--set-gtid-purged=OFF",
            f"--host={config['HOST']}", f"--port={config['PORT']}",
            f"--user={config['USER']}", config["NAME"]]
    try:
        with temporary_path.open("wb") as output:
            result = subprocess.run(argv, stdout=output, stderr=subprocess.PIPE,
                                    env=environment, timeout=300, check=False)
        if result.returncode:
            raise RuntimeError(f"mysqldump failed with exit code {result.returncode}")
        data = temporary_path.read_bytes()
        if data.count(b"CREATE TABLE") != len(tables) or b"DROP DATABASE" in data or b"USE `crm_db`" in data:
            raise RuntimeError("Dump content validation failed")
        digest = hashlib.sha256(data).hexdigest()
        temporary_path.replace(output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
        environment.pop("MYSQL_PWD", None)
    print(f"EXPORT PASS path={output_path} tables={len(tables)} bytes={len(data)} sha256={digest}")


if __name__ == "__main__":
    main()
