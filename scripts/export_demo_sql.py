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
    from apps.catalog.models import Brand, Category, Product
    from apps.catalog.management.commands.seed_catalog import PRODUCTS, IMAGES, INACTIVE_PRODUCTS
    from apps.catalog.management.commands.seed_demo import demo_emails, TITLES, PASSWORD, validate_demo_surveys
    from apps.feedback.models import Feedback
    from apps.surveys.models import Survey, SurveyResponse

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
            if not model._meta.proxy and model._meta.app_label in {"accounts", "catalog", "customers", "feedback", "surveys"}:
                cursor.execute(f"SELECT COUNT(*) FROM {connection.ops.quote_name(model._meta.db_table)}")
                if not cursor.fetchone()[0]:
                    raise ExportError(f"Run seed_demo on the disposable source before export: {model._meta.db_table} is empty")

    expected_emails = set(demo_emails())
    if set(Account.objects.values_list("email", flat=True)) != expected_emails:
        raise ExportError("Source accounts differ from seed_demo; refusing possible personal data")
    if any(not account.check_password(PASSWORD) for account in Account.objects.all()):
        raise ExportError("Demo password verification failed")
    if {role: Account.objects.filter(role__role_code=role, status='ACTIVE').count() for role in ('ADMIN','MANAGER','CUSTOMER')} != {'ADMIN':2,'MANAGER':3,'CUSTOMER':15}:
        raise ExportError("Demo role counts differ")
    if set(Product.objects.values_list("product_name", flat=True)) != {row[2] for row in PRODUCTS}:
        raise ExportError("Source products differ from the real seed_catalog")
    for product in Product.objects.select_related('category','brand'):
        expected = next(row for row in PRODUCTS if row[2] == product.product_name)
        if product.status != ('INACTIVE' if product.product_name in INACTIVE_PRODUCTS else 'ACTIVE'):
            raise ExportError('Catalog availability differs from the preserved baseline')
        if (product.category.category_name, product.brand.brand_name, str(int(product.price)), product.image_url) != (expected[0], expected[1], expected[4], IMAGES.get(expected[2], '')):
            raise ExportError("Catalog prices, images or relations differ")
    if set(Survey.objects.values_list('title',flat=True)) != set(TITLES):
        raise ExportError("Survey titles differ from seed_demo")
    if Feedback.objects.count()!=20 or Feedback.objects.filter(status='NEW').count()!=8 or Feedback.objects.filter(status='RESOLVED').count()!=12:
        raise ExportError("Feedback counts differ")
    if {s:Survey.objects.filter(status=s).count() for s in ('DRAFT','ACTIVE','CLOSED')} != {'DRAFT':3,'ACTIVE':7,'CLOSED':8} or SurveyResponse.objects.filter(status='SUBMITTED').count()!=61:
        raise ExportError("Survey counts differ")
    validate_demo_surveys()
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
        # Generate the data-only companion from the same inspected source. Explicit
        # columns support migration-created schemas; ignored duplicate PKs make a
        # second import leave every existing row unchanged. Fresh demo DBs only.
        seed_result = subprocess.run([*argv[:-1], '--no-create-info', '--complete-insert',
            '--insert-ignore', '--skip-add-locks', '--skip-disable-keys', config['NAME']],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment, timeout=300, check=False)
        if seed_result.returncode or not re.search(rb'INSERT\s+IGNORE\s+INTO `accounts`', seed_result.stdout):
            raise ExportError('Data-only export failed; canonical SQL has not been replaced')
        (ROOT / 'database' / 'seed_survey_report.sql').write_bytes(
            b'-- DEMO ONLY: import after migrations into an empty dedicated database; never into real data.\n' + seed_result.stdout)
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
