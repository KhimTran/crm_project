"""Create a full, portable pre-rebuild backup of crm_db.

Run with the project virtualenv. The output is intentionally outside Git.
"""

import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


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
        raise RuntimeError("Backup source must be the configured MySQL crm_db")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME, ENGINE FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'"
        )
        engines = cursor.fetchall()
        row_counts = {}
        for table, _ in engines:
            if not table.replace("_", "").isalnum():
                raise RuntimeError("Unexpected table name in source database")
            cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
            row_counts[table] = cursor.fetchone()[0]
    if not engines or any(engine != "InnoDB" for _, engine in engines):
        raise RuntimeError("All source tables must use InnoDB for a consistent dump")

    bin_dir = os.getenv("MYSQL_BIN")
    executable = (Path(bin_dir) / "mysqldump.exe") if bin_dir else shutil.which("mysqldump")
    if not executable or not Path(executable).is_file():
        raise RuntimeError("mysqldump is unavailable")
    directory = ROOT / "database" / "backups"
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"crm_db_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}_{uuid4().hex[:8]}.sql"
    final_path = directory / filename
    temporary_path = directory / (filename + ".partial")
    environment = os.environ.copy()
    environment["MYSQL_PWD"] = config["PASSWORD"] or ""
    argv = [
        str(executable), "--single-transaction", "--quick", "--no-tablespaces",
        "--default-character-set=utf8mb4", "--set-gtid-purged=OFF",
        "--routines", "--events", "--triggers",
        f"--host={config['HOST']}", f"--port={config['PORT']}",
        f"--user={config['USER']}", config["NAME"],
    ]
    try:
        with temporary_path.open("wb") as output:
            result = subprocess.run(argv, stdout=output, stderr=subprocess.PIPE,
                                    env=environment, timeout=300, check=False)
        if result.returncode:
            raise RuntimeError(f"mysqldump failed with exit code {result.returncode}")
        data = temporary_path.read_bytes()
        if len(data) < 1024 or data.count(b"CREATE TABLE") < len(engines):
            raise RuntimeError("Dump is missing expected table definitions")
        if not {"accounts", "customers", "products", "suppliers", "survey_recipients", "survey_responses"}.issubset(row_counts):
            raise RuntimeError("Required business tables are missing from source")
        digest = hashlib.sha256(data).hexdigest()
        temporary_path.replace(final_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
        environment.pop("MYSQL_PWD", None)
    print(f"Backup: {final_path}")
    print(f"Tables: {len(engines)}; bytes: {len(data)}; sha256: {digest}")
    print("Rows: " + ", ".join(f"{table}={row_counts[table]}" for table in sorted(row_counts)))


if __name__ == "__main__":
    main()
