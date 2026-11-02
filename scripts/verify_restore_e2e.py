"""Real Admin POST verification on a disposable MySQL database."""
import os,json,subprocess,tempfile,logging.config
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection
from django.test import Client,override_settings
from apps.admin_portal.services.backup_service import _inspect_dump, backup_manifest_path
from apps.admin_portal.services.restore_service import database_fingerprint
source=Path(os.environ.get('CRM_RESTORE_SOURCE','database/crm_db.sql')).resolve()
output=Path(os.environ.get('CRM_AUDIT_OUT','docs/crm_audit_20261101/completion')).resolve()
output.mkdir(parents=True,exist_ok=True)
settings.LOGGING['handlers']['database_operations']['filename']=output/'restore_operations.log'
logging.config.dictConfig(settings.LOGGING)
db=settings.DATABASES['default']; original=db['NAME']
name='crm_restore_e2e_'+uuid4().hex[:10]
params=connection.get_connection_params(); params.pop('database',None)
root=connection.Database.connect(**params); cursor=root.cursor()
root.select_db(original)
production_before=database_fingerprint(root)
cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
env=os.environ.copy(); env['MYSQL_PWD']=db['PASSWORD']
argv=['mysql.exe','--host='+db['HOST'],'--port='+str(db['PORT']),'--user='+db['USER'],'--default-character-set=utf8mb4',name]
def load(path):
    with path.open('rb') as stream: subprocess.run(argv,stdin=stream,env=env,check=True)
def publish(path,content):
    path.write_bytes(content); size,digest=_inspect_dump(path)
    backup_manifest_path(path).write_text(json.dumps({'version':1,'size_bytes':size,'sha256':digest}))
try:
    load(source)
    connection.close(); db['NAME']=name; connection.settings_dict['NAME']=name
    with tempfile.TemporaryDirectory() as directory, override_settings(BASE_DIR=Path(directory),ALLOWED_HOSTS=['testserver']):
        backups=Path(directory)/'database/backups'; backups.mkdir(parents=True)
        publish(backups/'selected.sql',source.read_bytes())
        connection.ensure_connection(); baseline=database_fingerprint(connection.connection)
        client=Client(enforce_csrf_checks=True)
        def login():
            client.get('/admin/login/')
            assert client.post('/admin/login/',{'email':'demo-admin@example.test','password':'DemoPass!2026','csrfmiddlewaretoken':client.cookies['csrftoken'].value}).status_code==302
        def restore(filename):
            return client.post('/admin/database/restore/',{'filename':filename,'target_database':name,'restore_confirm':f'RESTORE {filename} TO {name}','maintenance_ack':'on','csrfmiddlewaretoken':client.cookies['csrftoken'].value})
        login()
        with connection.cursor() as c: c.execute("UPDATE brands SET brand_name='RESTORE_SENTINEL' WHERE brand_id=1")
        response=restore('selected.sql')
        assert response.status_code==200 and b'Restore Successful' in response.content
        connection.close(); connection.ensure_connection()
        assert database_fingerprint(connection.connection)==baseline
        print('RESTORE_SENTINEL -> Yonex; all 22 tables match after reconnect')
        login(); before=database_fingerprint(connection.connection)
        for filename,content in [('broken.sql',source.read_bytes()+b'\nINVALID SQL;\n'),('schema.sql',b'-- MySQL dump 10.13\n-- Schema-only verification fixture without business data or INSERT statements.\nCREATE TABLE empty_demo (id INT);\n-- Dump completed on 2026-11-01\n')]:
            publish(backups/filename,content)
            assert restore(filename).status_code==302
            assert database_fingerprint(connection.connection)==before
        (backups/'invalid.sql').write_text('not a dump')
        assert restore('invalid.sql').status_code==302
        content=source.read_bytes()+(f"\nUPDATE brands SET brand_name='PARTIAL_IMPORT' WHERE brand_id=1;\nSET @qa=IF(DATABASE()='{name}','INVALID SQL','SELECT 1');\nPREPARE qa FROM @qa; EXECUTE qa;\n").encode()
        publish(backups/'partial.sql',content)
        marker=backups/'.restore-recovery.json'
        real_run=subprocess.run
        observed=[]; damaged_backup=[]
        def observe_real_import(*args, **kwargs):
            result=real_run(*args, **kwargs)
            if args[0][-1]==name and result.returncode:
                probe=connection.Database.connect(**{**params,'database':name})
                q=probe.cursor(); q.execute('SELECT brand_name FROM brands WHERE brand_id=1')
                observed.append(q.fetchone()[0]); q.close(); probe.close()
                if damage_recovery:
                    state=json.loads(marker.read_text())
                    path=backups/state['recovery_backup']
                    damaged_backup.append((path,path.read_bytes()))
                    path.write_bytes(path.read_bytes()+b'\n-- simulated damaged recovery media\n')
            return result
        with connection.cursor() as q:
            q.execute("UPDATE brands SET brand_name='BEFORE_FAILED_RESTORE' WHERE brand_id=1")
        before=database_fingerprint(connection.connection)
        damage_recovery=False
        with patch('subprocess.run',side_effect=observe_real_import):
            result=restore('partial.sql')
        assert result.status_code==409 and b'automatically recovered and verified' in result.content
        assert observed==['PARTIAL_IMPORT'], observed
        assert not marker.exists()
        connection.close(); connection.ensure_connection()
        assert database_fingerprint(connection.connection)==before
        assert client.get('/admin/database/').status_code==200
        print('Real failed import: PARTIAL_IMPORT; automatic recovery: BEFORE_FAILED_RESTORE; all tables match original fingerprint')
        # Fail closed when the retained backup is damaged; no fake mysql results.
        damage_recovery=True
        with patch('subprocess.run',side_effect=observe_real_import):
            assert restore('partial.sql').status_code==503
        assert marker.exists() and client.get('/admin/database/').status_code==503
        path,original_bytes=damaged_backup[-1]
        path.write_bytes(original_bytes)
        load(path)
        connection.close(); connection.ensure_connection()
        assert database_fingerprint(connection.connection)==before
        marker.unlink()
        print('Damaged recovery backup: RECOVERY_FAILED, HTTP blocked; operator recovery verified exact state')
        log=Path(settings.LOGGING['handlers']['database_operations']['filename']).read_text(encoding='utf-8')
        for event in ['RESTORE_SUCCESS','RESTORE_FAILED','RECOVERY_STARTED','RECOVERY_SUCCESS','RECOVERY_FAILED']:
            assert any(event in line and name in line for line in log.splitlines()), event
        print('Five required event types verified in database/operations.log for',name)
finally:
    connection.close(); db['NAME']=original; connection.settings_dict['NAME']=original
    cursor.execute(f'DROP DATABASE `{name}`')
    assert database_fingerprint(root)==production_before, 'Shared database changed during test'
    print('Shared crm_db fingerprint unchanged')
    cursor.close(); root.close()
