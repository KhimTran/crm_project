"""Read-only live checks; restore/migration rehearsals write only owned clone databases."""
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test.utils import CaptureQueriesContext
from apps.accounts.models import Account
from apps.accounts.selectors import list_account_page
from apps.admin_portal.services.backup_service import create_database_backup,verify_database_backup
from apps.admin_portal.services.restore_service import database_fingerprint
from verify_role_integrity import verify


def main():
    config=settings.DATABASES['default']; original=config['NAME']
    assert (original,config['HOST'],str(config['PORT']))==('crm_db','127.0.0.1','3306')
    root=connection.Database.connect(**connection.get_connection_params())
    cursor=root.cursor(); before=database_fingerprint(root)
    output=Path('docs/role_refactor/hardening')
    initial=json.loads((output/'environment.json').read_text(encoding='utf8'))
    assert {t:list(v) for t,v in before.items()}==initial['before_fingerprints'], 'Live data changed since initial snapshot'
    report={}

    def restore_verify(path,legacy):
        manifest=verify_database_backup(path)
        name='crm_role_verify_'+uuid4().hex[:12]
        cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        try:
            env=os.environ.copy(); env['MYSQL_PWD']=config['PASSWORD'] or ''
            argv=[str(Path(settings.MYSQL_BIN)/'mysql.exe'),'--host='+config['HOST'],'--port='+str(config['PORT']),
                  '--user='+config['USER'],'--default-character-set=utf8mb4',name]
            with path.open('rb') as stream:
                subprocess.run(argv,stdin=stream,env=env,check=True,stdout=subprocess.DEVNULL)
            connection.close(); config['NAME']=name; connection.settings_dict['NAME']=name
            connection.ensure_connection(); restored=database_fingerprint(connection.connection)
            if not legacy: assert restored==before, 'Current backup restore differs'
            with connection.cursor() as c:
                c.execute('SELECT role_id,role_code,description,created_at,updated_at FROM roles')
                role_reference=sorted(repr(tuple(r)) for r in c.fetchall())
            baseline={'fingerprints':json.loads(json.dumps(restored)), 'role_reference':role_reference}
            call_command('migrate',interactive=False,verbosity=0)
            executor=MigrationExecutor(connection)
            assert not executor.migration_plan(executor.loader.graph.leaf_nodes())
            if legacy:
                result=verify(baseline)
                call_command('migrate','accounts','0004',interactive=False,verbosity=0)
                call_command('migrate',interactive=False,verbosity=0)
                result['reverse_forward_reverified']=verify(baseline)['accounts_preserved']==20
            else:
                assert database_fingerprint(connection.connection)==restored
                result={'all_table_values_restored_identically':True,'existing_role_id_schema_no_pending_migration':True}
            return {'backup':path.name,'sha256':manifest['sha256'],'result':result}
        finally:
            connection.close(); config['NAME']=original; connection.settings_dict['NAME']=original
            cursor.execute(f'DROP DATABASE `{name}`')

    try:
        backup=create_database_backup(purpose='role_merge_readiness_verification')
        report['normalized_backup']=restore_verify(backup,False)
        report['legacy_backup']=restore_verify(Path('database/backups/crm_261104_135013.sql'),True)
        # Read-only projection against the original migration baseline, including every FK.
        report['live_integrity']=verify(json.loads(Path('docs/role_refactor/preflight_v2.json').read_text(encoding='utf8')))
        actor=Account.objects.filter(role__role_code='ADMIN').first()
        report['account_list_queries']={}
        for size in (1,20):
            with CaptureQueriesContext(connection) as queries:
                list_account_page(actor,page_size=size)
            report['account_list_queries'][str(size)]=len(queries)
        assert report['account_list_queries']['1']==report['account_list_queries']['20']
        report['live_fingerprints_unchanged']=database_fingerprint(root)==before
        assert report['live_fingerprints_unchanged']
        report['status']='PASS'
    finally:
        (output/'integrity_restore.json').write_text(json.dumps(report,indent=2),encoding='utf8')
        cursor.close(); root.close()
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
