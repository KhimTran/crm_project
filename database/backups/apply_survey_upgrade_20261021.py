"""Apply the rehearsed additive migrations under the local HTTP maintenance lock."""
import os
import sys
import json
import hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection
from django.core.management import call_command
from apps.admin_portal.services.maintenance import database_access
from apps.admin_portal.services.backup_service import verify_database_backup

path = ROOT / 'database/backups/survey_upgrade_20261021_report.json'
report = json.loads(path.read_text(encoding='utf-8'))
assert settings.DATABASES['default']['NAME'] == report['source'] == 'crm_db_v2'
assert report['restore_verified'] and report['rehearsal_verified']
verify_database_backup(ROOT / 'database/backups' / report['backup'])

def fingerprints():
    results = {}
    with connection.cursor() as cur:
        for table, fields in report['columns'].items():
            if table == 'django_migrations':
                continue
            selected = ','.join('`' + f + '`' for f in fields)
            cur.execute(f'SELECT {selected} FROM `{table}`')
            rows = sorted(repr(row) for row in cur.fetchall())
            results[table] = [len(rows), hashlib.sha256(repr(rows).encode()).hexdigest()]
    return results

with database_access(exclusive=True):
    before = fingerprints()
    expected = {t:v for t,v in report['before'].items() if t != 'django_migrations'}
    assert before == expected, 'Source changed since backup; take a new verified backup'
    call_command('migrate', 'surveys', interactive=False)
    assert fingerprints() == before, 'Pre-existing data differs after migration'
    report['source_migration_verified'] = True
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('PASS live migration; every pre-existing column value preserved')
call_command('check')
call_command('showmigrations', 'surveys')
call_command('migrate', plan=True)

from django.test import RequestFactory
from django.urls import resolve
from django.contrib.messages.storage.fallback import FallbackStorage
from apps.accounts.models import Account
user = Account.objects.filter(role='MANAGER', status='ACTIVE').first()
assert user, 'No active Manager account for render verification'
for url in ['/surveys/manage/', '/manager/']:
    request = RequestFactory().get(url, HTTP_HOST='127.0.0.1:8000')
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    match = resolve(url)
    response = match.func(request, *match.args, **match.kwargs)
    if url == '/manager/':
        assert response.status_code == 302
        destination = response.url
        request = RequestFactory().get(destination, HTTP_HOST='127.0.0.1:8000')
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        match = resolve(destination)
        response = match.func(request, *match.args, **match.kwargs)
        assert response.status_code == 200, (destination, response.status_code)
        print('PASS Manager home redirect', destination)
    assert response.status_code == 200, (url, response.status_code)
    print('PASS Manager page render', url, response.status_code)
