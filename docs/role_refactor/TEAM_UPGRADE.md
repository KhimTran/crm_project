# Team upgrade and restore guide

Use the project virtualenv, confirm `.env` points to your intended host/database without publishing its password, and keep existing data. This guide does not authorize changes to a shared database. Coordinate its maintenance window and operator first.

## Inspect before choosing a path

```powershell
git status --short
git fetch origin
git pull --ff-only
.\venv\Scripts\python.exe manage.py showmigrations accounts
.\venv\Scripts\python.exe manage.py migrate --plan
.\venv\Scripts\python.exe manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('SHOW COLUMNS FROM accounts'); print([r[0] for r in c.fetchall()])"
```

Preserve other people's uncommitted work. Stop if schema and migration history disagree, if both `role` and `role_id` remain after an interrupted DDL operation, or if foundational migrations before accounts.0004 have not been reconciled. Do not use `--fake`, flush, recreate the database, delete migrations or import a dump over populated tables to make the checks pass.

## 1. Existing database already has role_id

For a database with accounts.0005–0007 applied and the actual FK to roles.role_id, this hardening introduces **no migration** and needs no data conversion or seed. Check:

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe manage.py migrate --plan
```

The plan should be empty. Restart workers after updating the code. Role resolution reads existing rows; it does not recreate missing configuration. If a standard Role is missing, investigate first. An operator can explicitly run `manage.py initialize_roles` to add only missing standard Roles; it leaves existing labels, IDs and Accounts unchanged and is idempotent. Do not run it automatically on requests or infer an Account's role from a missing FK.

## 2. Existing database still has the role VARCHAR column

For the verified pre-refactor foundation (accounts.0004 applied), stop HTTP workers, scheduled jobs and external writers. Create a full backup before migration:

```powershell
.\venv\Scripts\python.exe manage.py shell -c "from apps.admin_portal.services.backup_service import create_database_backup,verify_database_backup; p=create_database_backup(purpose='team_role_upgrade'); verify_database_backup(p); print(p.name)"
```

This creates SQL and its checksum manifest only in database/backups/. Integrity verification alone is not a restore test. Restore the exact file into a **new empty disposable database** first. The existing guarded helper refuses an existing destination:

```text
python scripts/restore_disposable.py database/backups/YOUR_BACKUP.sql crm_db_backup_verify YOUR_SHA256
```

Replace placeholders with the verified filename and manifest SHA256. If that destination already exists, stop and arrange a different empty review database; do not delete somebody else's database. Inspect migration SQL and apply on the clone first:

```powershell
$env:DB_NAME='crm_db_backup_verify'
.\venv\Scripts\python.exe manage.py migrate --plan
.\venv\Scripts\python.exe manage.py sqlmigrate accounts 0005
.\venv\Scripts\python.exe manage.py sqlmigrate accounts 0006
.\venv\Scripts\python.exe manage.py sqlmigrate accounts 0007
.\venv\Scripts\python.exe manage.py migrate --noinput
$env:PYTHONPATH='.'
$env:CRM_AUDIT_OUT='docs/role_refactor/team_verification'
.\venv\Scripts\python.exe scripts/run_crm_audit.py
```

The audit runner creates a unique test database and checks the source fingerprint. Verify row values, Account IDs/email/password hashes/status/profiles/timestamps, role-code mapping and all FKs on your clone. MySQL ON UPDATE timestamps must stay unchanged during backfill. Only after restore, migration, regression and integrity checks pass, with authorization for your database and a controlled maintenance window, point DB_NAME back to the intended source and apply `manage.py migrate --noinput`. Verify schema/data and restart workers. Do not leave the environment pointing to the clone. Do not use the dated, environment-specific deploy_role_normalization.py as a generic team deployment command.

## 3. Brand-new database

Create a separately named empty MySQL database with utf8mb4/utf8mb4_unicode_ci and a suitably scoped user. Point DB_NAME to it, run `manage.py migrate --noinput`, then `manage.py check`. Migration 0005 initializes the three standard Roles by code, so creating normal users/superusers works without implicit runtime writes to roles. IDs are not fixed.

Use `createsuperuser` only when an operator intends to create an Admin. Optional `seed_demo` is for a dedicated demo database only, never a populated or shared database. No seed is needed to deploy the hardening.

## 4. Restore an older backup

Never import a DROP TABLE dump over the current populated database. Keep that database and the verified backup intact. Restore first into a new isolated destination with the guarded helper, including django_migrations, Groups, permission mappings and sessions. Inspect restored physical columns and migration history. For VARCHAR schema, follow path 2 on the restored clone before exposing it to new code. For an already normalized schema, follow path 1. Unknown or inconsistent history requires investigation, not fake/reset.

Old source code expecting `account.role` as a string is not compatible with the new Python model. New code reads `account.role_code`; ORM expressions use `role__role_code`. APIs/forms still use the same string `role` field. Coordinate code and schema together; do not run old workers against the contracted schema.

## Recovery

MySQL DDL can commit implicitly. If any stage fails, keep traffic stopped, retain the backup and exact failure/migration history, and inspect completed DDL. A completed normalization was reverse/forward tested on clones; reverse migrations require baseline code before traffic resumes. Partial DDL needs an operator-reviewed repair plan. A validated recovery clone can establish the source for recovery; do not reset or overwrite the original database as an automatic fallback.

See [REPORT.md](REPORT.md), [hardening/REPORT.md](hardening/REPORT.md), and [database schema and data dictionary](../database_schema.md).
