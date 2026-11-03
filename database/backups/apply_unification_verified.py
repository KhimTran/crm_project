import json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.test_account_unification import snapshot,verify,connection,MigrationExecutor
from django.conf import settings
from django.core.management import call_command
from django.db import transaction
from django.test import Client,override_settings
from apps.admin_portal.services.backup_service import create_database_backup,verify_database_backup
from apps.admin_portal.services.maintenance import database_access
import MySQLdb

assert connection.settings_dict['NAME']=='crm_db_v2'
assert connection.settings_dict['HOST']=='127.0.0.1'
assert str(connection.settings_dict['PORT'])=='3306'
with database_access(exclusive=True):
    executor=MigrationExecutor(connection)
    assert ('accounts','0004_remove_staff_account_account_address_and_more') not in executor.loader.applied_migrations
    before=snapshot()
    assert 'migration_profile_archive' not in before
    backup=create_database_backup(purpose='verified_local_account_unification')
    manifest=verify_database_backup(backup)
    private=MySQLdb.connect(host='127.0.0.1',port=33072,user='root',passwd='',charset='utf8mb4')
    target='crm_unification_final_restore_20261022'
    with private.cursor() as c:
        c.execute('CREATE DATABASE `crm_unification_final_restore_20261022` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    exe=Path(settings.MYSQL_BIN.strip(chr(34)+chr(39)))/'mysql.exe'
    with backup.open('rb') as f:
        r=subprocess.run([str(exe),'--host=127.0.0.1','--port=33072','--user=root',target],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert r.returncode==0,'Final backup restore failed'
    private.select_db(target)
    with private.cursor() as c:
        for table,rows in before.items():
            if table=='__foreign_keys__':continue
            c.execute('SELECT * FROM `'+table+'`')
            columns=[r[0] for r in c.description]
            restored=[dict(zip(columns,row)) for row in c.fetchall()]
            assert sorted(rows,key=repr)==sorted(restored,key=repr),'Final restore mismatch: '+table
    private.close()
    assert before==snapshot(),'Source changed during backup verification'
    print('FINAL BACKUP RESTORE VERIFIED',backup.name,manifest['sha256'],flush=True)
    run={'backup':str(backup),'manifest':manifest,'restore_target':target,'revision':'9a93f6b + uncommitted migration fixes'}
    Path('database/backups/unification_final_run.json').write_text(json.dumps(run,indent=2))
    marker=Path('database/backups/.restore-recovery.json')
    marker.write_text(json.dumps(dict(run,operation='account_unification',status='in_progress'),indent=2))
    call_command('migrate',interactive=False,verbosity=1)
    verify(before)
    assert not MigrationExecutor(connection).migration_plan(MigrationExecutor(connection).loader.graph.leaf_nodes())
    page_before=snapshot()
    from apps.accounts.models import Account
    admin=Account.objects.filter(role='ADMIN',status='ACTIVE').first()
    customer=Account.objects.filter(role='CUSTOMER',status='ACTIVE').first()
    assert admin is not None and customer is not None
    with override_settings(ALLOWED_HOSTS=['testserver','127.0.0.1','localhost']):
        with transaction.atomic():
            client=Client()
            client.force_login(admin)
            response=client.get('/admin/accounts/')
            assert response.status_code==200
            assert admin.email.encode() in response.content
            client.logout()
            assert client.get('/admin/accounts/').status_code==302
            client.force_login(customer)
            assert client.get('/admin/accounts/').status_code==403
            transaction.set_rollback(True)
    assert page_before==snapshot(),'HTTP smoke test changed persisted data'
    marker.unlink()
    print('LOCAL PASS: all original rows/FKs verified; /admin/accounts/ ADMIN 200, anonymous 302, CUSTOMER 403; HTTP test writes rolled back',flush=True)
