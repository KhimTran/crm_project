"""Import a verified project dump into a new, allowlisted disposable MySQL DB."""

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


TARGETS = {"crm_db_backup_verify", "crm_db_dump_verify"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dump", type=Path)
    parser.add_argument("target", choices=sorted(TARGETS))
    parser.add_argument("sha256")
    args = parser.parse_args()
    source = args.dump.resolve(strict=True)
    allowed_roots = ((ROOT / "database" / "backups").resolve(), (ROOT / "database").resolve())
    if not source.is_file() or source.suffix.lower() != ".sql" or not any(source.is_relative_to(root) for root in allowed_roots):
        raise RuntimeError("Dump must be a regular SQL file inside project database directory")
    data = source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != args.sha256.lower() or len(data) < 1024:
        raise RuntimeError("Dump SHA-256 or size validation failed")
    if re.search(rb"(?im)^\s*(CREATE|DROP)\s+DATABASE\b|^\s*USE\s+", data):
        raise RuntimeError("Dump selects or changes a database")
    if b"CREATE TABLE" not in data:
        raise RuntimeError("Dump has no table definitions")

    config = settings.DATABASES["default"]
    if config["ENGINE"] != "django.db.backends.mysql" or config["NAME"] != "crm_db":
        raise RuntimeError("Source configuration must point to the real crm_db")
    bin_dir = os.getenv("MYSQL_BIN")
    executable = (Path(bin_dir) / "mysql.exe") if bin_dir else shutil.which("mysql")
    if not executable or not Path(executable).is_file():
        raise RuntimeError("mysql executable is unavailable")
    import MySQLdb

    admin = MySQLdb.connect(host=config["HOST"], port=int(config["PORT"]),
                            user=config["USER"], passwd=config["PASSWORD"], charset="utf8mb4")
    try:
        cursor = admin.cursor()
        cursor.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s", [args.target])
        if cursor.fetchone():
            raise RuntimeError(f"Disposable database {args.target} already exists")
        cursor.execute(f"CREATE DATABASE `{args.target}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    finally:
        admin.close()

    environment = os.environ.copy()
    environment["MYSQL_PWD"] = config["PASSWORD"] or ""
    argv = [str(executable), "--default-character-set=utf8mb4",
            f"--host={config['HOST']}", f"--port={config['PORT']}",
            f"--user={config['USER']}", args.target]
    try:
        with source.open("rb") as input_file:
            result = subprocess.run(argv, stdin=input_file, stderr=subprocess.PIPE,
                                    env=environment, timeout=300, check=False)
        if result.returncode:
            raise RuntimeError(f"mysql import failed with exit code {result.returncode}")
    finally:
        environment.pop("MYSQL_PWD", None)
    print(f"RESTORE PASS target={args.target} source={source} sha256={digest}")


if __name__ == "__main__":
    main()
