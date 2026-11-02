"""Verified, owner-authorized cleanup of the configured crm_db only."""
import os,json,subprocess
from pathlib import Path
from uuid import uuid4
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection
from django.core.management import call_command
from apps.admin_portal.services.backup_service import create_database_backup,verify_database_backup
from apps.admin_portal.services.restore_service import database_fingerprint
from apps.admin_portal.services.maintenance import database_access,recovery_marker_path

db=settings.DATABASES['default']; original=db['NAME']
assert original=='crm_db'
env=os.environ.copy(); env['MYSQL_PWD']=db['PASSWORD']
args=['--host='+db['HOST'],'--port='+str(db['PORT']),'--user='+db['USER'],'--default-character-set=utf8mb4']
name='crm_style_cleanup_verify_'+uuid4().hex[:10]
def inspect():
    connection.ensure_connection()
    return database_fingerprint(connection.connection)
def verify(before, after):
    for table in before:
        if table not in ('customer_preferences','django_migrations'):
            assert after[table]==before[table], 'Unexpected data change: '+table
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM customer_preferences WHERE preference_type='PLAY_STYLE'")
        assert cursor.fetchone()[0]==0
        cursor.execute("SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=DATABASE() AND CONSTRAINT_NAME='chk_customer_preferences_type' AND CONSTRAINT_TYPE='CHECK'")
        assert cursor.fetchone()[0]==1

with database_access(exclusive=True):
    before=inspect()
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM customer_preferences WHERE preference_type<>%s ORDER BY preference_id',['PLAY_STYLE'])
        preserved=cursor.fetchall()
        cursor.execute("SELECT k.TABLE_NAME,k.COLUMN_NAME,k.REFERENCED_TABLE_NAME,k.REFERENCED_COLUMN_NAME,c.IS_NULLABLE,r.DELETE_RULE,r.UPDATE_RULE FROM information_schema.KEY_COLUMN_USAGE k JOIN information_schema.COLUMNS c ON c.TABLE_SCHEMA=k.TABLE_SCHEMA AND c.TABLE_NAME=k.TABLE_NAME AND c.COLUMN_NAME=k.COLUMN_NAME JOIN information_schema.REFERENTIAL_CONSTRAINTS r ON r.CONSTRAINT_SCHEMA=k.CONSTRAINT_SCHEMA AND r.TABLE_NAME=k.TABLE_NAME AND r.CONSTRAINT_NAME=k.CONSTRAINT_NAME WHERE k.TABLE_SCHEMA=DATABASE() AND k.REFERENCED_TABLE_NAME IS NOT NULL")
        fks=cursor.fetchall()
        assert not any(row[2]=='customer_preferences' for row in fks), 'Unexpected dependent FK'
    backup=create_database_backup(purpose='before_supported_preference_schema')
    verify_database_backup(backup)
    params=connection.get_connection_params(); params.pop('database',None)
    control=connection.Database.connect(**params); cursor=control.cursor()
    cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    with backup.open('rb') as stream:
        subprocess.run(['mysql.exe',*args,name],stdin=stream,env=env,check=True)
    try:
        connection.close(); db['NAME']=name; connection.settings_dict['NAME']=name
        assert inspect()==before,'Backup recovery mismatch'
        print('All backup tables restored and verified:',backup.name)
        call_command('migrate','customers','0004_supported_preference_types',verbosity=1,interactive=False)
        verify(before,inspect())
        with connection.cursor() as probe:
            probe.execute('SELECT * FROM customer_preferences ORDER BY preference_id')
            assert probe.fetchall()==preserved
        print('Disposable migration verified; supported preference rows unchanged')
    finally:
        connection.close(); db['NAME']=original; connection.settings_dict['NAME']=original
        cursor.execute(f'DROP DATABASE `{name}`'); cursor.close(); control.close()
    assert inspect()==before,'Shared DB changed during rehearsal'
    marker=recovery_marker_path()
    marker.write_text(json.dumps({'database':original,'recovery_backup':backup.name,'state':'play_style_cleanup_in_progress'}))
    call_command('migrate','customers','0004_supported_preference_types',verbosity=1,interactive=False)
    verify(before,inspect())
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM customer_preferences ORDER BY preference_id')
        assert cursor.fetchall()==preserved
        for source,column,target,target_column,*rest in fks:
            cursor.execute(f'SELECT COUNT(*) FROM `{source}` s LEFT JOIN `{target}` t ON s.`{column}`=t.`{target_column}` WHERE s.`{column}` IS NOT NULL AND t.`{target_column}` IS NULL')
            assert cursor.fetchone()[0]==0,(source,column)
    marker.unlink()
    print('Live cleanup verified; removed rows:',before['customer_preferences'][1]-len(preserved))
    with Path('database/crm_db.sql').open('wb') as out:
        subprocess.run(['mysqldump.exe',*args,'--single-transaction','--no-tablespaces',original],stdout=out,env=env,check=True)
    with connection.cursor() as cursor:
        cursor.execute('SHOW TABLES')
        business=[row[0] for row in cursor.fetchall() if not row[0].startswith(('django_','auth_'))]
    with Path('database/seed_survey_report.sql').open('wb') as out:
        subprocess.run(['mysqldump.exe',*args,'--single-transaction','--no-tablespaces','--no-create-info','--skip-add-locks','--insert-ignore','--skip-disable-keys',original,*business],stdout=out,env=env,check=True)
    clean_backup=create_database_backup(purpose='after_supported_preference_schema')
    verify_database_backup(clean_backup)
    print('Clean backup:',clean_backup.name)
