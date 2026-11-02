"""Unmodified full suite on a unique MySQL test DB; preserve structured evidence."""
import os,json,logging.config,unittest,time
from pathlib import Path
from uuid import uuid4
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection
from django.test.runner import DiscoverRunner
from apps.admin_portal.services.restore_service import database_fingerprint

OUT=Path(os.environ.get('CRM_AUDIT_OUT', 'docs/crm_audit_20261101/completion')); OUT.mkdir(parents=True,exist_ok=True)
settings.LOGGING['handlers']['database_operations']['filename']=(OUT/'test_operations.log').resolve()
logging.config.dictConfig(settings.LOGGING)
connection.ensure_connection()
before=database_fingerprint(connection.connection)
params=connection.get_connection_params()
observer=connection.Database.connect(**params)
test_database='test_crm_audit_'+uuid4().hex[:10]
settings.DATABASES['default'].setdefault('TEST',{})['NAME']=test_database
rows=[]
class Result(unittest.TextTestResult):
    def record(self,test,state,detail=''):
        prior=next((row for row in rows if row['test']==test.id()),None)
        if prior:
            prior['state']=state
            prior['detail']+='\n'+detail
        else:
            rows.append({'test':test.id(),'state':state,'detail':detail})
        (OUT/'full_suite.json').write_text(json.dumps({'results':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    def addSuccess(self,test): super().addSuccess(test); self.record(test,'PASS')
    def addFailure(self,test,err): super().addFailure(test,err); self.record(test,'FAIL',self._exc_info_to_string(err,test))
    def addError(self,test,err): super().addError(test,err); self.record(test,'ERROR',self._exc_info_to_string(err,test))
    def addSkip(self,test,reason): super().addSkip(test,reason); self.record(test,'SKIP',reason)
    def addSubTest(self,test,subtest,err):
        super().addSubTest(test,subtest,err)
        if err:
            self.record(test,'FAIL' if issubclass(err[0],test.failureException) else 'ERROR',str(subtest)+'\n'+self._exc_info_to_string(err,test))
class TextRunner(unittest.TextTestRunner):
    def __init__(self,*args,**kwargs): kwargs['resultclass']=Result; super().__init__(*args,**kwargs)
    def run(self,test):
        result=super().run(test)
        self.summary={'tests_run':result.testsRun,'failure_issues':len(result.failures),'error_issues':len(result.errors)}
        (OUT/'unittest_totals.json').write_text(json.dumps(self.summary,indent=2),encoding='utf-8')
        return result
class Runner(DiscoverRunner):
    test_runner=TextRunner
    def setup_databases(self,**kwargs):
        # Discovery imports config/test_settings.py; enforce isolation afterwards.
        settings.DATABASES['default'].setdefault('TEST',{})['NAME']=test_database
        connection.settings_dict.setdefault('TEST',{})['NAME']=test_database
        return super().setup_databases(**kwargs)
started=time.monotonic()
try:
    failed=Runner(verbosity=2,interactive=False).run_tests([])
finally:
    unchanged=database_fingerprint(observer)==before
    observer.close()
    (OUT/'suite_summary.json').write_text(json.dumps({'counts':{state:sum(r['state']==state for r in rows) for state in ['PASS','FAIL','ERROR','SKIP']},'duration_seconds':round(time.monotonic()-started,2),'live_database_unchanged':unchanged,'test_database':test_database},indent=2),encoding='utf-8')
    assert unchanged,'Shared crm_db data changed during tests'
