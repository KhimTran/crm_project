"""Deploy only to the owner's local demo, after recorded clone and test gates."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from apps.admin_portal.services.backup_service import create_database_backup, verify_database_backup
from apps.admin_portal.services.maintenance import database_access, recovery_marker_path
from apps.admin_portal.services.restore_service import database_fingerprint, verified_import_snapshot
from verify_role_integrity import verify


def main():
    assert sys.argv[1:] == ['--deploy-local'], 'Explicit local deployment argument required'
    output = Path('docs/role_refactor')
    suite = json.loads((output/'verified/suite_summary.json').read_text())
    assert suite['counts'] == {'PASS': 509, 'FAIL': 0, 'ERROR': 0, 'SKIP': 0}, 'Full regression gate failed'
    assert suite['live_database_unchanged'], 'Test isolation gate failed'
    assert json.loads((output/'clone_integrity.json').read_text(encoding='utf8'))['accounts_preserved'] == 20
    http = json.loads((output/'http/http_flows.json').read_text(encoding='utf8'))
    failures = [row for row in http if row['status'] != 'PASS']
    # Preserve the audit failure, and require separate reproduction using baseline source.
    assert len(http) == 15 and len(failures) == 1
    assert failures[0]['case'] == 'CLI demo seed cleanup'
    assert failures[0]['error'] == 'CommandError: Final demo dataset detected. Use seed_demo; legacy report fixtures are separate.'
    assert json.loads((output/'http/baseline_seed_guard.json').read_text())['original_command_reproduces_same_rejection']
    config = settings.DATABASES['default']
    assert (config['NAME'], config['HOST'], str(config['PORT'])) == ('crm_db','127.0.0.1','3306')
    report = {'status': 'NOT_STARTED'}
    with database_access(exclusive=True):
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT @@hostname')
            assert cursor.fetchone()[0] == 'DESKTOP-HE9BDKO', 'Unexpected server'
            cursor.execute('SELECT ID FROM information_schema.PROCESSLIST WHERE DB=DATABASE() AND ID<>CONNECTION_ID()')
            assert not cursor.fetchall(), 'Other local database clients must stop before deployment'
            cursor.execute("SELECT EVENT_NAME FROM information_schema.EVENTS WHERE EVENT_SCHEMA=DATABASE() AND STATUS='ENABLED'")
            assert not cursor.fetchall(), 'Uncontrolled scheduled writers'
        baseline = json.loads((output/'preflight_v2.json').read_text(encoding='utf8'))
        before = database_fingerprint(connection.connection)
        assert all(list(before[t]) == value for t,value in baseline['fingerprints'].items()), 'Source changed since verified rehearsal'
        backup = create_database_backup(purpose='role_deployment_recovery')
        manifest = verify_database_backup(backup)
        env = os.environ.copy(); env['MYSQL_PWD'] = config['PASSWORD'] or ''
        executable = Path(settings.MYSQL_BIN)/'mysql.exe'
        argv = [str(executable),'--host='+config['HOST'],'--port='+str(config['PORT']),
                '--user='+config['USER'],'--default-character-set=utf8mb4',config['NAME']]
        with verified_import_snapshot(backup, executable, argv, env) as restored:
            assert restored == before, 'Deployment backup restore differs'
        report.update(recovery_backup=backup.name, sha256=manifest['sha256'], backup_restore_verified=True)
        try:
            report['status'] = 'MIGRATING'
            call_command('migrate', interactive=False, verbosity=1)
            report.update(verify(baseline))
            report['status'] = 'DEPLOYED_VERIFIED'
        except Exception:
            report['status'] = 'RECOVERY_REQUIRED'
            recovery_marker_path().write_text(json.dumps(report,indent=2),encoding='utf8')
            raise
        finally:
            (output/'deployment.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
