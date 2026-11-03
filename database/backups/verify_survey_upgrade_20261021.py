"""Local operational rehearsal; no credentials or row values are printed."""
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
import MySQLdb
from django.conf import settings
from django.db import connection
from apps.admin_portal.services.backup_service import verify_database_backup

BACKUP = ROOT / 'database/backups/crm_db_v2_20261021_073715_f8cec295.sql'
TARGET = 'test_crm_review_20261016_8b99'
config = settings.DATABASES['default']
assert config['NAME'] == 'crm_db_v2'
manifest = verify_database_backup(BACKUP)
data = BACKUP.read_bytes()
assert b'CREATE DATABASE' not in data and b'\nUSE ' not in data

def connect(name):
    return MySQLdb.connect(host=config['HOST'], port=int(config['PORT']),
        user=config['USER'], passwd=config['PASSWORD'], db=name, charset='utf8mb4')

def snapshot(db, columns=None):
    cur = db.cursor()
    if columns is None:
        cur.execute('SHOW TABLES')
        columns = {}
        for (table,) in cur.fetchall():
            cur.execute(f'SHOW COLUMNS FROM `{table}`')
            columns[table] = [r[0] for r in cur.fetchall()]
    fingerprints = {}
    for table, fields in columns.items():
        selected = ','.join('`' + f + '`' for f in fields)
        cur.execute(f'SELECT {selected} FROM `{table}`')
        rows = sorted(repr(row) for row in cur.fetchall())
        fingerprints[table] = [len(rows), hashlib.sha256(repr(rows).encode()).hexdigest()]
    return columns, fingerprints

source = connect(config['NAME'])
columns, before = snapshot(source)
cur = source.cursor()
cur.execute('SELECT k.TABLE_NAME,k.COLUMN_NAME,k.REFERENCED_TABLE_NAME,k.REFERENCED_COLUMN_NAME,c.IS_NULLABLE,r.DELETE_RULE FROM information_schema.KEY_COLUMN_USAGE k JOIN information_schema.COLUMNS c ON c.TABLE_SCHEMA=k.TABLE_SCHEMA AND c.TABLE_NAME=k.TABLE_NAME AND c.COLUMN_NAME=k.COLUMN_NAME JOIN information_schema.REFERENTIAL_CONSTRAINTS r ON r.CONSTRAINT_SCHEMA=k.CONSTRAINT_SCHEMA AND r.CONSTRAINT_NAME=k.CONSTRAINT_NAME AND r.TABLE_NAME=k.TABLE_NAME WHERE k.TABLE_SCHEMA=%s AND k.REFERENCED_TABLE_NAME IS NOT NULL', [config['NAME']])
foreign_keys = cur.fetchall()
cur.execute('SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s', [TARGET])
assert cur.fetchone() is None, 'Refusing to overwrite an existing database'
cur.execute(f'CREATE DATABASE `{TARGET}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
source.close()
environment = os.environ.copy()
environment['MYSQL_PWD'] = config['PASSWORD'] or ''
mysql = Path(os.environ['MYSQL_BIN']) / 'mysql.exe'
with BACKUP.open('rb') as stream:
    result = subprocess.run([str(mysql), '--default-character-set=utf8mb4',
        '--host=' + config['HOST'], '--port=' + str(config['PORT']),
        '--user=' + config['USER'], TARGET], stdin=stream,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment, timeout=120)
assert result.returncode == 0, 'Disposable import failed'
restored = connect(TARGET)
assert snapshot(restored, columns)[1] == before, 'Restored data differs'
restored.close()
print('PASS full backup restore: all table data matches')
environment.pop('MYSQL_PWD', None)
environment['DB_NAME'] = TARGET
result = subprocess.run([sys.executable, str(ROOT / 'manage.py'), 'migrate', 'surveys', '--noinput'],
    cwd=ROOT, env=environment, timeout=120)
assert result.returncode == 0, 'Rehearsal migration failed'
restored = connect(TARGET)
preserved_columns = {t: f for t, f in columns.items() if t != 'django_migrations'}
assert snapshot(restored, preserved_columns)[1] == {t:v for t,v in before.items() if t != 'django_migrations'}, 'Existing data changed'
restored.close()
report = dict(source=config['NAME'], target=TARGET, backup=BACKUP.name,
    sha256=manifest['sha256'], revision='bde440f405b6cd4b99068c020a0e5e535dfe2fe4',
    columns=columns, before=before, foreign_keys=foreign_keys,
    restore_verified=True, rehearsal_verified=True)
(ROOT / 'database/backups/survey_upgrade_20261021_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('PASS migration rehearsal: all pre-existing values preserved; target=' + TARGET)
