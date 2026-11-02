"""Rehearse legacy rating CHECK repair; never migrate the shared database."""
import os,json,subprocess,tempfile
from pathlib import Path
from uuid import uuid4
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection,transaction,IntegrityError
from django.core.management import call_command
from apps.admin_portal.services.restore_service import database_fingerprint
from apps.surveys.models import SurveyAnswer

out=Path('docs/crm_audit_20261101/completion'); out.mkdir(parents=True,exist_ok=True)
db=settings.DATABASES['default']; original=db['NAME']
params=connection.get_connection_params(); root=connection.Database.connect(**params)
before=database_fingerprint(root); cursor=root.cursor()
names=['crm_schema_audit_'+uuid4().hex[:10], 'crm_schema_backup_'+uuid4().hex[:10], 'crm_schema_fresh_'+uuid4().hex[:10]]
env=os.environ.copy(); env['MYSQL_PWD']=db['PASSWORD']
flags=['--host='+db['HOST'],'--port='+str(db['PORT']),'--user='+db['USER'],'--default-character-set=utf8mb4']
result={'databases':names}
try:
    for name in names:
        cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    with Path('database/crm_db.sql').open('rb') as source:
        subprocess.run(['mysql.exe',*flags,names[0]],stdin=source,env=env,check=True)
    connection.close(); db['NAME']=names[0]; connection.settings_dict['NAME']=names[0]
    # Reproduce the physical CHECK present in live SQL before this fix.
    with connection.cursor() as c:
        c.execute('ALTER TABLE survey_answers DROP CHECK chk_survey_answers_rating_1_10')
        c.execute('ALTER TABLE survey_answers ADD CONSTRAINT chk_survey_answers_rating CHECK (rating_value IS NULL OR rating_value BETWEEN 1 AND 5)')
    baseline=database_fingerprint(connection.connection)
    with tempfile.TemporaryDirectory(prefix='crm_schema_backup_') as directory:
        backup=Path(directory)/'before.sql'
        with backup.open('wb') as stream:
            subprocess.run(['mysqldump.exe',*flags,'--single-transaction','--routines','--triggers','--hex-blob',names[0]],stdout=stream,env=env,check=True)
        with backup.open('rb') as stream:
            subprocess.run(['mysql.exe',*flags,names[1]],stdin=stream,env=env,check=True)
        observer=connection.Database.connect(**{**params,'database':names[1]})
        assert database_fingerprint(observer)==baseline
        observer.close()
        result['pre_migration_backup_restore_verified']=True
        call_command('migrate',interactive=False,verbosity=0)
        after=database_fingerprint(connection.connection)
        assert {k:v for k,v in baseline.items() if k!='django_migrations'}=={k:v for k,v in after.items() if k!='django_migrations'}
        result['all_existing_rows_preserved']=True
        with connection.cursor() as c:
            c.execute("SELECT CONSTRAINT_NAME,CHECK_CLAUSE FROM information_schema.CHECK_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=DATABASE() AND CONSTRAINT_NAME LIKE 'chk_survey_answers_rating%'")
            result['checks_after']=c.fetchall()
        assert len(result['checks_after'])==1 and '1_10' in result['checks_after'][0][0]
        sample=SurveyAnswer.objects.filter(rating_value__isnull=False).first()
        with transaction.atomic():
            SurveyAnswer.objects.filter(pk=sample.pk).update(rating_value=10)
            assert SurveyAnswer.objects.get(pk=sample.pk).rating_value==10
            try:
                with transaction.atomic():
                    SurveyAnswer.objects.filter(pk=sample.pk).update(rating_value=11)
            except IntegrityError:
                result['rejects_rating_11']=True
            else:
                raise AssertionError('CHECK allowed 11')
            transaction.set_rollback(True)
        result['rating_10_round_trip']=True
        # Data-only SQL must also work on tables physically built by migrations.
        from apps.accounts.models import Account
        demo=Account.objects.filter(email__endswith='@survey-report-demo.test').values_list('account_id','full_name','date_of_birth')
        expected=list(demo)
        import sqlparse
        with connection.cursor() as c:
            for statement in sqlparse.split(Path('database/seed_survey_report.sql').read_text(encoding='utf-8')):
                if statement.strip(): c.execute(statement)
        assert list(demo)==expected
        result['idempotent_seed_snapshot']=True
        connection.close(); db['NAME']=names[2]; connection.settings_dict['NAME']=names[2]
        call_command('migrate',interactive=False,verbosity=0)
        with connection.cursor() as c:
            for statement in sqlparse.split(Path('database/seed_survey_report.sql').read_text(encoding='utf-8')):
                if statement.strip(): c.execute(statement)
        fresh=list(Account.objects.filter(email__endswith='@survey-report-demo.test').values_list('account_id','full_name','date_of_birth'))
        assert fresh==expected, (fresh[:2],expected[:2])
        result['seed_on_fresh_migrated_schema_matches_dump']=True
finally:
    connection.close(); db['NAME']=original; connection.settings_dict['NAME']=original
    for name in names: cursor.execute(f'DROP DATABASE `{name}`')
    result['live_database_unchanged']=database_fingerprint(root)==before
    cursor.close(); root.close()
    (out/'schema_reconciliation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    assert result['live_database_unchanged']
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
