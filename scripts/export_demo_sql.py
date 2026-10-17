"""Export only a freshly migrated and seeded disposable MySQL demo database.

Set DB_NAME to the disposable source, then run, for example:
python scripts/export_demo_sql.py --source-db crm_db_review_export_20261016_8b99 \
    --confirm-demo-source crm_db_review_export_20261016_8b99
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

class ExportError(RuntimeError):
    """An export guard failed; this message is safe to show to the operator."""


def parse_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-db", required=True, help="Disposable MySQL source configured by DB_NAME")
    parser.add_argument(
        "--confirm-demo-source", required=True, metavar="SOURCE_DB",
        help="Repeat the source name to confirm it was freshly migrated and seeded only for this export",
    )
    args = parser.parse_args()
    if (
        not re.fullmatch(r"crm_db_[A-Za-z0-9_]+", args.source_db)
        or not {"test", "demo", "export"}.intersection(args.source_db.split("_"))
        or args.confirm_demo_source != args.source_db
    ):
        parser.error("Confirm a dedicated crm_db_* test/demo/export source; shared crm_db is forbidden")
    return args


def inspect_source(connection):
    from django.apps import apps
    from django.db.migrations.executor import MigrationExecutor

    from apps.accounts.models import Account
    from apps.catalog.management.commands.seed_data import SUPPLIERS
    from apps.catalog.models import Brand, Category, Product, Supplier
    from apps.customers.seed import DEMO_CUSTOMER_COUNT, demo_email
    from apps.surveys.models import Survey

    executor = MigrationExecutor(connection)
    executor.loader.check_consistent_history(connection)
    expected_migrations = set(executor.loader.graph.nodes)
    applied_migrations = set(executor.loader.applied_migrations)
    missing = expected_migrations - applied_migrations
    unexpected = applied_migrations - expected_migrations
    if missing or unexpected or executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise ExportError(
            f"Migration history differs from this revision: missing={sorted(missing)}, unexpected={sorted(unexpected)}"
        )

    expected_tables = {
        model._meta.db_table for model in apps.get_models(include_auto_created=True)
        if model._meta.managed and not model._meta.proxy
    } | {"django_migrations"}
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_TYPE='BASE TABLE'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        if tables != expected_tables:
            raise ExportError("Disposable demo source does not contain exactly this revision's expected tables")
        for table in (
            "django_session", "django_admin_log", "auth_group", "auth_group_permissions",
            "accounts_groups", "accounts_user_permissions",
        ):
            cursor.execute(f"SELECT COUNT(*) FROM {connection.ops.quote_name(table)}")
            if cursor.fetchone()[0]:
                raise ExportError(f"Demo export requires an empty {table} table")
        for model in apps.get_models():
            if model._meta.app_label in {"accounts", "catalog", "customers", "feedback", "surveys"}:
                cursor.execute(f"SELECT COUNT(*) FROM {connection.ops.quote_name(model._meta.db_table)}")
                if not cursor.fetchone()[0]:
                    raise ExportError(f"Run seed_data on the disposable source before export: {model._meta.db_table} is empty")

    expected_emails = {"demo-admin@example.test", "demo-customer@example.test"} | {
        demo_email(index) for index in range(1, DEMO_CUSTOMER_COUNT + 1)
    }
    if set(Account.objects.values_list("email", flat=True)) != expected_emails:
        raise ExportError("Source accounts differ from seed_data; refusing possible personal data")
    if set(Supplier.objects.values_list("supplier_code", flat=True)) != {code for code, _ in SUPPLIERS}:
        raise ExportError("Source suppliers differ from seed_data")
    if set(Product.objects.values_list("product_name", flat=True)) != {
        f"Demo racket {index}" for index in range(1, len(SUPPLIERS) + 1)
    }:
        raise ExportError("Source products differ from seed_data")
    for queryset, expected in (
        (Category.objects.values_list("category_name", flat=True), {"Badminton rackets"}),
        (Brand.objects.values_list("brand_name", flat=True), {"Demo brand"}),
        (Survey.objects.values_list("title", flat=True), {"Demo badminton survey"}),
    ):
        if set(queryset) != expected:
            raise ExportError("Source catalog/survey data differs from seed_data")
    return tables, len(expected_migrations)


def export_demo(config, tables, migration_count):
    bin_dir = os.getenv("MYSQL_BIN")
    executable = (Path(bin_dir) / "mysqldump.exe") if bin_dir else shutil.which("mysqldump")
    if not executable or not Path(executable).is_file():
        raise ExportError("mysqldump is unavailable")
    output_path = ROOT / "database" / "crm_db.sql"
    environment = os.environ.copy()
    environment["MYSQL_PWD"] = config["PASSWORD"] or ""
    argv = [str(executable), "--single-transaction", "--quick", "--no-tablespaces",
            "--default-character-set=utf8mb4", "--set-gtid-purged=OFF",
            f"--host={config['HOST'] or '127.0.0.1'}", f"--port={config['PORT'] or '3306'}",
            f"--user={config['USER']}", config["NAME"]]
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output_path.parent, prefix="crm_db_", suffix=".sql.partial", delete=False,
        ) as output:
            temporary_path = Path(output.name)
            result = subprocess.run(argv, stdout=output, stderr=subprocess.PIPE,
                                    env=environment, timeout=300, check=False, shell=False)
        if result.returncode:
            raise ExportError(f"mysqldump failed with exit code {result.returncode}; stderr withheld")
        data = temporary_path.read_bytes()
        dumped_tables = {
            name.decode("utf-8") for name in re.findall(rb"^CREATE TABLE `([^`]+)`", data, re.MULTILINE)
        }
        forbidden = rb"^\s*(?:(?:CREATE|DROP|ALTER)\s+DATABASE|USE\s|CREATE\s+USER|GRANT\s)|DEFINER\s*="
        if (
            dumped_tables != tables
            or re.search(forbidden, data, re.MULTILINE | re.IGNORECASE)
            or b"-- Dump completed on" not in data
        ):
            raise ExportError("Dump content validation failed; canonical SQL has not been replaced")
        digest = hashlib.sha256(data).hexdigest()
        temporary_path.replace(output_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
        environment.pop("MYSQL_PWD", None)
    print(
        f"EXPORT PASS source={config['NAME']} path={output_path} tables={len(tables)} "
        f"migrations={migration_count} bytes={len(data)} sha256={digest}"
    )


def main():
    args = parse_arguments()
    import django

    django.setup()
    from django.conf import settings
    from django.db import DatabaseError, connection
    from django.db.migrations.exceptions import InconsistentMigrationHistory

    try:
        config = settings.DATABASES["default"]
        if config["ENGINE"] != "django.db.backends.mysql" or config["NAME"] != args.source_db:
            raise ExportError("Configured DB_NAME must match the confirmed disposable MySQL source")
        tables, migration_count = inspect_source(connection)
        export_demo(config, tables, migration_count)
    except ExportError as exc:
        print(f"EXPORT FAILED: {exc}", file=sys.stderr)
        return 1
    except (DatabaseError, InconsistentMigrationHistory):
        print("EXPORT FAILED: cannot verify disposable source database/migration state", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("EXPORT FAILED: mysqldump timed out; canonical SQL has not been replaced", file=sys.stderr)
        return 1
    except OSError:
        print("EXPORT FAILED: cannot execute mysqldump or write/publish the SQL output", file=sys.stderr)
        return 1
    finally:
        connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
