"""Owner-authorized live reconciliation with independently verified recovery media."""
import os,json,subprocess,shutil,logging,getpass
from pathlib import Path
from uuid import uuid4
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection,transaction,IntegrityError
from django.core.management import call_command
from django.db.migrations.executor import MigrationExecutor
from apps.admin_portal.services.backup_service import create_database_backup,verify_database_backup,backup_manifest_path,get_backup_dir
from apps.admin_portal.services.restore_service import database_fingerprint
from apps.admin_portal.services.maintenance import database_access
from apps.surveys.models import SurveyAnswer
import sqlparse

log=logging.getLogger('apps.admin_portal.finalization')
db=settings.DATABASES['default']; assert db['NAME']=='crm_db'
operator=getpass.getuser(); result={'operator':operator,'seed_added':0}
params=connection.get_connection_params(); control=connection.Database.connect(**params); c=control.cursor()
env=os.environ.copy(); env['MYSQL_PWD']=db['PASSWORD']
args=['--host='+db['HOST'],'--port='+str(db['PORT']),'--user='+db['USER'],'--default-character-set=utf8mb4']
def fp():
    connection.ensure_connection(); return database_fingerprint(connection.connection)
def clone_verify(path,expected,seed=False):
    name='crm_finalize_'+uuid4().hex[:10]
    c.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    try:
        with path.open('rb') as stream: subprocess.run(['mysql.exe',*args,name],stdin=stream,env=env,check=True,capture_output=True)
        connection.close(); db['NAME']=name; connection.settings_dict['NAME']=name
        assert fp()==expected,'Restore fingerprint mismatch'
        if seed:
            with connection.cursor() as q:
                q.execute('SELECT TABLE_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL')
                for table,col,target,key in q.fetchall():
                    q.execute(f'SELECT COUNT(*) FROM `{table}` s LEFT JOIN `{target}` t ON s.`{col}`=t.`{key}` WHERE s.`{col}` IS NOT NULL AND t.`{key}` IS NULL'); assert q.fetchone()[0]==0
            sample=SurveyAnswer.objects.filter(rating_value__isnull=False).first()
            with transaction.atomic():
                SurveyAnswer.objects.filter(pk=sample.pk).update(rating_value=10)
                assert SurveyAnswer.objects.get(pk=sample.pk).rating_value==10
                try:
                    with transaction.atomic(): SurveyAnswer.objects.filter(pk=sample.pk).update(rating_value=11)
                except IntegrityError: pass
                else: raise AssertionError('11 accepted')
                transaction.set_rollback(True)
            for _ in range(2):
                with connection.cursor() as q:
                    for statement in sqlparse.split(Path('database/seed_survey_report.sql').read_text(encoding='utf-8')):
                        if statement.strip(): q.execute(statement)
                assert fp()==expected,'Seed changed existing snapshot'
    finally:
        connection.close(); db['NAME']='crm_db'; connection.settings_dict['NAME']='crm_db'
        c.execute(f'DROP DATABASE `{name}`')

try:
    with database_access(exclusive=True):
        before=fp(); result['before']=before
        recovery=Path('database/recovery')/uuid4().hex; recovery.mkdir(parents=True)
        pre=create_database_backup(purpose='finalize_pre_migration')
        saved=recovery/pre.name; shutil.copy2(pre,saved); shutil.copy2(backup_manifest_path(pre),backup_manifest_path(saved))
        verify_database_backup(saved); clone_verify(saved,before)
        result['recovery_backup']=str(saved)
        log.info('FINALIZE_PRE_BACKUP SUCCESS operator=%s path=%s restore_verified=true',operator,saved)
        call_command('migrate',interactive=False,verbosity=1)
        after=fp()
        assert all(after[t]==value for t,value in before.items() if t!='django_migrations')
        assert not MigrationExecutor(connection).migration_plan(MigrationExecutor(connection).loader.graph.leaf_nodes())
        log.info('FINALIZE_MIGRATION SUCCESS operator=%s migration=surveys.0006_reconcile_rating_constraint rows_preserved=true',operator)
        # Export exactly live state, including routines/events/triggers and technical tables.
        full=create_database_backup(purpose='finalize_full_backup')
        verify_database_backup(full); clone_verify(full,after,seed=True)
        shutil.copy2(full,'database/crm_db.sql')
        result.update(after=after,backup=str(full),manifest=json.loads(backup_manifest_path(full).read_text()),restore_verified=True,seed_idempotent=True)
        log.info('FINALIZE_SEED SUCCESS operator=%s added=0 two_imports_fingerprint_unchanged=true',operator)
        directory=get_backup_dir().resolve(); deleted=[]
        for path in directory.glob('*.sql'):
            assert path.resolve().parent==directory
            if path.resolve()!=full.resolve():
                path.unlink(); deleted.append(path.name)
                backup_manifest_path(path).unlink(missing_ok=True)
        result['deleted']=deleted
        log.info('FINALIZE SUCCESS operator=%s file=%s size=%s sha256=%s restore_verified=true deleted=%s',operator,full.name,result['manifest']['size_bytes'],result['manifest']['sha256'],deleted)
except Exception:
    log.exception('FINALIZE FAILED operator=%s recovery_backup=%s',operator,result.get('recovery_backup'))
    raise
finally:
    Path('docs/crm_audit_20261101/completion/finalize_database.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    c.close(); control.close()
