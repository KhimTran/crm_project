"""Real HTTP/CSRF/ORM cross-role audit against an isolated MySQL clone."""
import os,json,subprocess,tempfile,time,urllib.request,urllib.parse,urllib.error,http.cookiejar,logging.config,traceback
from pathlib import Path
from uuid import uuid4
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection
from django.utils import timezone
from apps.admin_portal.services.restore_service import database_fingerprint
from apps.accounts.models import Account
from apps.catalog.models import Product
from apps.feedback.models import Feedback
from apps.surveys.models import Survey,SurveyQuestion,SurveyOption,SurveyRecipient,SurveyResponse,SurveyAnswer
from apps.customers.reports import favorite_brand_report,age_group_report
OUT=Path(os.environ.get('CRM_AUDIT_OUT', 'docs/crm_audit_20261101/completion')).resolve(); OUT.mkdir(parents=True,exist_ok=True)
db=settings.DATABASES['default']; original=db['NAME']; name='crm_http_audit_'+uuid4().hex[:10]
params=connection.get_connection_params(); root=connection.Database.connect(**params); before=database_fingerprint(root)
cursor=root.cursor(); cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
env=os.environ.copy(); env['MYSQL_PWD']=db['PASSWORD']
with Path('database/crm_db.sql').open('rb') as source:
    subprocess.run(['mysql.exe','--host='+db['HOST'],'--port='+str(db['PORT']),'--user='+db['USER'],'--default-character-set=utf8mb4',name],stdin=source,env=env,check=True)
connection.close(); db['NAME']=name; connection.settings_dict['NAME']=name
PW='AuditStrong!2026'; rows=[]
def case(label,action):
    try: detail=action(); row={'case':label,'status':'PASS','evidence':detail}
    except Exception as exc: row={'case':label,'status':'FAIL','error':f'{type(exc).__name__}: {exc}','traceback':traceback.format_exc()}
    rows.append(row); (OUT/'http_flows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8'); print(row,flush=True)
class Browser:
    def __init__(self): self.jar=http.cookiejar.CookieJar(); self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
    def request(self,path,data=None,headers=None):
        headers=headers or {}
        if data is not None:
            headers['X-CSRFToken']=next((c.value for c in self.jar if c.name=='csrftoken'),'')
            data=urllib.parse.urlencode(data,doseq=True).encode()
        request=urllib.request.Request('http://127.0.0.1:8018'+path,data=data,headers=headers)
        try:
            response=self.opener.open(request,timeout=30); return response.status,response.geturl(),response.read().decode()
        except urllib.error.HTTPError as e: return e.code,e.geturl(),e.read().decode()
    def login(self,path,email):
        self.request(path); result=self.request(path,{'email':email,'password':PW}); assert result[0]==200 and '/login/' not in result[1],result[:2]
    def post(self,path,data): return self.request(path,data)
    def json(self, method, path, data=None, csrf=True):
        headers={'Content-Type':'application/json'}
        if csrf: headers['X-CSRFToken']=next((c.value for c in self.jar if c.name=='csrftoken'),'')
        request=urllib.request.Request('http://127.0.0.1:8018'+path, method=method,
            data=json.dumps(data or {}).encode(), headers=headers)
        try:
            response=self.opener.open(request,timeout=30)
            return response.status, response.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code,exc.read().decode()

process=None
try:
    admin=Account.objects.create_superuser('audit-admin@audit.test',PW)
    manager=Account.objects.create_user('audit-manager@audit.test',PW,role='MANAGER')
    customer=Account.objects.create_user('audit-customer@audit.test',PW,full_name='Audit Customer',playing_level='BEGINNER',date_of_birth='2000-01-01')
    product=Product.objects.filter(status='ACTIVE').first()
    with tempfile.TemporaryDirectory(prefix='crm_http_audit_') as directory:
        base=Path(directory); (base/'database/backups').mkdir(parents=True)
        module=base/'crm_http_settings.py'
        module.write_text('from config.settings import *\nBASE_DIR=Path('+repr(str(base))+')\nDATABASES["default"]["NAME"]='+repr(name)+'\nALLOWED_HOSTS=["127.0.0.1","localhost"]\nLOGGING["handlers"]["database_operations"]["filename"]='+repr(str(OUT/'http_operations.log'))+'\n',encoding='utf-8')
        childenv=os.environ.copy(); childenv['PYTHONPATH']=str(base)+os.pathsep+str(Path.cwd()); childenv['PYTHONIOENCODING']='utf-8'
        with (OUT/'http_server.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen([str(Path('venv/Scripts/python.exe').resolve()),'manage.py','runserver','127.0.0.1:8018','--noreload','--settings=crm_http_settings'],env=childenv,stdout=log,stderr=log)
            for _ in range(40):
                try: urllib.request.urlopen('http://127.0.0.1:8018/login/',timeout=1); break
                except Exception: time.sleep(.3)
            a,m,c=Browser(),Browser(),Browser()
            case('Role login',lambda:(a.login('/admin/login/',admin.email),m.login('/manager/login/',manager.email),c.login('/login/',customer.email),'3 real CSRF login flows'))
            def account_flow():
                data={'email':'audit-created@audit.test','password':PW,'password_confirm':PW,'role':'MANAGER','status':'ACTIVE'}
                a.post('/admin/accounts/create/',data)
                target=Account.objects.get(email=data['email']); assert target.role=='MANAGER' and target.check_password(PW)
                actor=Browser(); actor.login('/manager/login/',target.email)
                assert actor.request('/manager/')[0]==200
                denied=actor.request('/admin/accounts/'); assert denied[0]==403 or '/admin/login/' in denied[1]
                a.post(f'/admin/accounts/{target.pk}/role/',{'role':'CUSTOMER'}); target.refresh_from_db(); assert target.role=='CUSTOMER'
                result=actor.request('/manager/'); assert '/manager/login/' in result[1] or result[0]==403
                a.post('/admin/accounts/create/',data); assert Account.objects.filter(email=data['email']).count()==1
                a.post(f'/admin/accounts/{target.pk}/lock/',{}); target.refresh_from_db(); assert target.status=='LOCKED'
                a.post(f'/admin/accounts/{target.pk}/unlock/',{}); target.refresh_from_db(); assert target.status=='ACTIVE'
                a.post(f'/admin/accounts/{target.pk}/reset-password/',{'new_password':PW+'New','new_password_confirm':PW+'New'}); target.refresh_from_db(); assert target.check_password(PW+'New')
                a.post('/admin/accounts/create/',{**data,'email':'audit-created-admin@audit.test','role':'ADMIN'})
                created_admin=Account.objects.get(email='audit-created-admin@audit.test'); assert created_admin.role=='ADMIN'
                admin_actor=Browser(); admin_actor.login('/admin/login/',created_admin.email)
                return 'create/hash/duplicate/role change/old session/lock/unlock/reset verified by ORM'
            case('A Account lifecycle',account_flow)
            def customer_flow():
                result=m.post('/crm/customers/new/',{'email':'audit-newcustomer@audit.test','password':PW,'full_name':'Audit New Customer','phone':'0909876543','playing_level':'BEGINNER'})
                target=Account.objects.get(email='audit-newcustomer@audit.test'); assert target.full_name=='Audit New Customer'
                m.post(f'/crm/customers/{target.pk}/edit/',{'full_name':'Audit Edited Customer','email':target.email,'phone':'0909876543','playing_level':'BEGINNER'})
                target.refresh_from_db(); assert target.full_name=='Audit Edited Customer'
                actor=Browser(); actor.login('/login/',target.email)
                m.post(f'/crm/customers/{target.pk}/lock/',{}); target.refresh_from_db(); assert target.status=='LOCKED'
                blocked=Browser(); blocked.request('/login/')
                denied=blocked.post('/login/',{'email':target.email,'password':PW}); assert '/login/' in denied[1]
                assert actor.request('/account/profile/')[0] in (302,403) or '/login/' in actor.request('/account/profile/')[1]
                m.post(f'/crm/customers/{target.pk}/unlock/',{}); target.refresh_from_db(); assert target.status=='ACTIVE'
                blocked.login('/login/',target.email)
                m.post(f'/crm/customers/{target.pk}/delete/',{}); assert not Account.objects.filter(pk=target.pk).exists()
                return 'manager create/lock/stale session/unlock/hard-delete-without-history verified'
            case('B Customer lifecycle',customer_flow)
            def feedback_flow():
                result=c.post('/feedbacks/new/',{'product':product.pk,'rating':5,'content':'AUDIT feedback <script>window.auditXss=1</script>','customer_id':manager.pk,'status':'RESOLVED','handled_by':manager.pk})
                feedback=Feedback.objects.get(customer=customer,content__startswith='AUDIT feedback'); assert feedback.product_id==product.pk and feedback.rating==5
                assert feedback.status=='NEW' and feedback.handled_by_id is None and feedback.resolved_at is None
                m.post(f'/crm/feedbacks/{feedback.pk}/',{'status':'IN_PROGRESS','manager_note':'Retired status'})
                feedback.refresh_from_db(); assert feedback.status=='NEW' and feedback.manager_note is None
                page=m.request('/crm/feedbacks/?q=AUDIT')[2]; assert 'AUDIT feedback' in page and '<script>window.auditXss=1</script>' not in page
                m.post(f'/crm/feedbacks/{feedback.pk}/',{'status':'RESOLVED','manager_note':'Audit resolved'})
                feedback.refresh_from_db(); assert feedback.status=='RESOLVED' and feedback.manager_note=='Audit resolved' and feedback.handled_by_id==manager.pk and feedback.resolved_at is not None
                return {'feedback_id':feedback.pk,'status':feedback.status,'customer_id':feedback.customer_id,'product_id':feedback.product_id}
            case('C Customer feedback -> manager',feedback_flow)
            def survey_flow():
                today=timezone.localdate(); end=today+__import__('datetime').timedelta(days=7)
                questions=[{'text':'Bạn hài lòng về shop?','type':'SINGLE_CHOICE','required':True,'options':['Hài lòng','Cần cải thiện']}]
                data={'title':'AUDIT saved audience survey','objective':'SATISFACTION','start_at':today.isoformat(),'end_at':end.isoformat(),'audience':'pick','customer_ids':[customer.pk],'action':'save','questions_json':json.dumps(questions,ensure_ascii=False)}
                response=m.post('/surveys/manage/new/',data)
                survey=Survey.objects.get(title=data['title']); assert survey.audience['customer_ids']==[customer.pk]
                assert SurveyQuestion.objects.filter(survey=survey).count()==1
                page=m.request(f'/surveys/manage/{survey.pk}/audience/')[2]; assert 'name="customer_ids"' not in page
                m.post(f'/surveys/manage/{survey.pk}/audience/',{'action':'send','audience':'all'})
                recipient=SurveyRecipient.objects.get(survey=survey,customer=customer); assert SurveyRecipient.objects.filter(survey=survey).count()==1
                m.post(f'/surveys/manage/{survey.pk}/audience/',{'action':'send'}); assert SurveyRecipient.objects.filter(survey=survey).count()==1
                assert c.request(f'/surveys/recipients/{recipient.pk}/')[0]==200
                question=SurveyQuestion.objects.get(survey=survey); option=SurveyOption.objects.filter(question=question).first()
                result=c.post(f'/surveys/recipients/{recipient.pk}/submit/',{'answers':json.dumps([{'question_id':question.pk,'option_id':option.pk}])})
                stored=SurveyResponse.objects.get(recipient=recipient); assert stored.status=='SUBMITTED'
                assert SurveyAnswer.objects.filter(response=stored,option=option).count()==1
                c.post(f'/surveys/recipients/{recipient.pk}/submit/',{'answers':json.dumps([{'question_id':question.pk,'option_id':option.pk}])}); assert SurveyAnswer.objects.filter(response=stored).count()==1
                assert m.request(f'/surveys/manage/{survey.pk}/stats/')[0]==200
                from apps.surveys.services import build_stats
                stats=build_stats(survey)
                assert stats['responses']==1 and stats['done']==1 and stats['sent']==1
                assert stats['items'][0]['respondents']==1
                return {'survey_id':survey.pk,'recipient_id':recipient.pk,'submitted':1,'answers':1}
            case('D Saved audience survey -> answer -> stats',survey_flow)
            def reports():
                assert m.request('/crm/reports/customers/')[0]==200
                from apps.customers.models import CustomerPreference
                CustomerPreference.objects.create(customer=customer,preference_type='FAVORITE_BRAND',preference_value='Yonex')
                result=favorite_brand_report(); expected=CustomerPreference.objects.filter(preference_type='FAVORITE_BRAND',customer__role='CUSTOMER').values('customer_id').distinct().count()
                assert result['answered']==expected,(result,expected)
                assert 'Yonex' in m.request('/crm/reports/customers/')[2]
                with connection.cursor() as q:
                    q.execute('SELECT date_of_birth FROM accounts WHERE role=%s',['CUSTOMER'])
                    births=[r[0] for r in q.fetchall()]
                today=timezone.localdate(); buckets=[0]*7
                for birth in births:
                    if birth is None: buckets[6]+=1; continue
                    age=today.year-birth.year-((today.month,today.day)<(birth.month,birth.day))
                    index=0 if age<18 else 1 if age<25 else 2 if age<35 else 3 if age<45 else 4 if age<55 else 5
                    buckets[index]+=1
                rendered=age_group_report()
                assert [r['count'] for r in rendered]==buckets,(rendered,buckets)
                return {'favorite_answered':result['answered'],'direct_sql_expected':expected,'age_groups':rendered,'age_sql_buckets':buckets}
            case('E Customer reports SQL reconciliation',reports)
            def security():
                assert c.request('/api/accounts/')[0] in (401,403)
                denied=m.request('/admin/database/'); assert denied[0]==403 or '/admin/login/' in denied[1]
                result=c.post('/account/profile/',{'full_name':'Audit updated','phone':'0901234999','role':'ADMIN'})
                customer.refresh_from_db(); assert customer.full_name=='Audit updated' and customer.role=='CUSTOMER'
                assert c.request('/products/?q='+urllib.parse.quote("' OR 1=1 --"))[0]==200
                req=urllib.request.Request('http://127.0.0.1:8018/admin/database/restore/',data=b'filename=bad.sql')
                try: a.opener.open(req); raise AssertionError('CSRF accepted')
                except urllib.error.HTTPError as e: assert e.code==403
                foreign=SurveyRecipient.objects.exclude(customer=customer).first()
                assert c.request(f'/surveys/recipients/{foreign.pk}/')[0] in (403,404)
                return 'Customer admin API denied; Manager database denied; profile mass assignment ignored; SQLi-like search handled; no-CSRF POST rejected'
            case('Cross-role security and profile',security)
            def unified_login():
                outcomes=[]
                for account in [admin,manager]:
                    actor=Browser(); actor.request('/login/')
                    result=actor.post('/login/',{'email':account.email,'password':PW})
                    outcomes.append({'role':account.role,'url':result[1],'status':result[0]})
                assert all('/login/' not in result['url'] for result in outcomes),outcomes
                return outcomes
            case('Unified login routes staff session correctly',unified_login)
            def concurrent_logout():
                actor=Browser(); actor.login('/admin/login/',admin.email); actor.login('/manager/login/',manager.email)
                assert '/admin/login/' not in actor.request('/admin/')[1]
                actor.post('/manager/logout/',{})
                result=actor.request('/crm/customers/')
                assert result[0]==200 and '/login/' not in result[1], {'url':result[1],'cookies':[(cookie.name,cookie.value[:5]) for cookie in actor.jar]}
                return 'Admin CRM remains available after Manager logout'
            case('Concurrent sessions CRM after Manager logout',concurrent_logout)
            def admin_delete():
                target=Account.objects.create_user('audit-delete@audit.test',PW,role='MANAGER')
                a.post(f'/admin/accounts/{target.pk}/delete/',{})
                assert not Account.objects.filter(pk=target.pk).exists()
                return 'Admin UI hard delete unreferenced Manager, verified absent in DB'
            case('Admin delete unreferenced account',admin_delete)
            def registration():
                actor=Browser(); actor.request('/register/')
                data={'email':'audit-register@audit.test','password':PW,'password_confirm':PW,'full_name':'Audit Registered','phone':'0908765123','playing_level':'BEGINNER'}
                actor.post('/register/',data)
                target=Account.objects.get(email=data['email']); assert target.check_password(PW) and target.role=='CUSTOMER'
                actor.post('/logout/',{}); actor.request('/register/'); actor.post('/register/',data)
                assert Account.objects.filter(email=data['email']).count()==1
                return 'Actual registration form/hash/duplicate protection'
            case('Customer registration and duplicate',registration)
            def seed_cleanup():
                from django.core.management import call_command
                from io import StringIO
                output=StringIO()
                call_command('seed_survey_report_demo','--confirm',stdout=output)
                call_command('seed_survey_report_demo','--clear','--confirm',stdout=output)
                remaining=list(Account.objects.filter(email__endswith='@survey-report-demo.test').values('account_id','role','full_name'))
                assert not remaining,remaining
                return output.getvalue()
            case('CLI demo seed cleanup',seed_cleanup)
            def api_read():
                one=a.request('/api/accounts/?page=1&page_size=5')
                two=a.request('/api/accounts/?page=2&page_size=5')
                assert one[0]==200 and two[0]==200,(one[:2],two[:2])
                first=json.loads(one[2]); second=json.loads(two[2])
                ids=[row['account_id'] for row in first['items']+second['items']]
                assert ids==sorted(ids) and len(ids)==len(set(ids))
                assert all('password' not in row and 'password_hash' not in row for row in first['items'])
                invalid=a.request('/api/accounts/?page=garbage')
                assert invalid[0]==400,invalid[:2]
                return {'pages':2,'ids':ids,'invalid_page_status':400,'password_hash_exposed':False}
            case('Admin Accounts API pagination and validation',api_read)
            def api_mutations():
                payload={'email':'audit-json@audit.test','role':'CUSTOMER','status':'ACTIVE','password':PW,'password_confirm':PW}
                assert a.json('POST','/api/accounts/',payload,csrf=False)[0]==403
                assert m.json('POST','/api/accounts/',payload)[0] in (401,403)
                assert c.json('POST','/api/accounts/',payload)[0] in (401,403)
                invalid=a.json('POST','/api/accounts/',{**payload,'role':'INVALID'})
                assert invalid[0]==400,invalid
                created=a.json('POST','/api/accounts/',payload)
                assert created[0]==201,created
                target=Account.objects.get(email=payload['email']); assert target.check_password(PW)
                path=f'/api/accounts/{target.pk}'
                assert a.json('POST','/api/accounts/',payload)[0]==400
                assert a.json('PATCH',path,{'email':'bad@audit.test'})[0]==405
                assert a.json('POST',path+'/role',{'role':'ADMIN'})[0]==409
                assert a.json('POST',path+'/role',{'role':'manager'})[0]==200
                target.refresh_from_db(); assert target.role=='MANAGER'
                actor=Browser(); actor.login('/manager/login/',target.email)
                assert a.json('POST',path+'/lock')[0]==200
                target.refresh_from_db(); assert target.status=='LOCKED'
                assert '/login/' in actor.request('/manager/')[1]
                assert a.json('POST',path+'/unlock')[0]==200
                assert a.json('POST',path+'/reset-password',{'new_password':PW+'New','new_password_confirm':PW+'New'})[0]==200
                target.refresh_from_db(); assert target.check_password(PW+'New') and not target.check_password(PW)
                assert a.json('POST','/api/accounts/999999999/lock')[0]==404
                assert a.json('DELETE',path)[0]==200
                assert not Account.objects.filter(pk=target.pk).exists()
                return 'Real JSON create/duplicate/role policy/role change/lock/stale session/unlock/reset/delete; CSRF+Manager+Customer denied; DB values verified'
            case('JSON mutation API lifecycle, authorization and CSRF',api_mutations)
            def customer_json():
                path='/crm/customers/new/'
                payload={'email':'audit-json-customer@audit.test','full_name':'Audit JSON Customer',
                         'phone':'0905556677','password':PW,'playing_level':'BEGINNER'}
                response=m.request(path,{},headers={'Accept':'application/json'})
                assert response[0]==400 and 'errors' in json.loads(response[2])
                denied=c.request(path,payload,headers={'Accept':'application/json'})
                # urllib follows the role guard's redirect to the Customer home.
                assert denied[0]==200 and denied[1]=='http://127.0.0.1:8018/',denied[:2]
                assert not Account.objects.filter(email=payload['email']).exists()
                created=m.request(path,payload,headers={'Accept':'application/json'})
                assert created[0]==201,created[:2]
                parsed=json.loads(created[2]); target=Account.objects.get(email=payload['email'])
                assert target.full_name==payload['full_name'] and target.check_password(PW)
                assert PW not in created[2] and 'password_hash' not in created[2]
                duplicate=m.request(path,payload,headers={'Accept':'application/json'})
                assert duplicate[0] in (400,409)
                assert Account.objects.filter(email=payload['email']).count()==1
                assert payload['email'] in m.request('/crm/customers/?q='+urllib.parse.quote(payload['email']))[2]
                m.post(f'/crm/customers/{target.pk}/delete/',{})
                assert not Account.objects.filter(pk=target.pk).exists()
                return 'JSON response contract: invalid 400, unauthorized denied, create 201 and DB round-trip, duplicate rejected, refreshed list and cleanup'
            case('Customer JSON mutation form contract',customer_json)
            process.terminate(); process.wait(timeout=15); process=None
finally:
    if process: process.terminate(); process.wait(timeout=15)
    connection.close(); db['NAME']=original; connection.settings_dict['NAME']=original
    cursor.execute(f'DROP DATABASE `{name}`'); unchanged=database_fingerprint(root)==before
    cursor.close(); root.close()
    (OUT/'http_isolation.json').write_text(json.dumps({'database':name,'live_database_unchanged':unchanged}),encoding='utf-8')
    assert unchanged,'Shared crm_db changed during HTTP audit'
