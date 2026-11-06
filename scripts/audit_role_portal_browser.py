"""Actual Edge portal forms on an owned disposable MySQL clone, never live writes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request
from uuid import uuid4
from contextlib import ExitStack

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection
from apps.accounts.models import Account
from apps.catalog.models import Product
from apps.admin_portal.services.restore_service import database_fingerprint
from browser_cdp import DevTools

OUT=Path(os.environ.get('CRM_AUDIT_OUT','docs/role_refactor/hardening/browser_portals')).resolve()
OUT.mkdir(parents=True,exist_ok=True)
db=settings.DATABASES['default']; original=db['NAME']
root=connection.Database.connect(**connection.get_connection_params()); before=database_fingerprint(root)
cursor=root.cursor(); name='crm_role_browser_'+uuid4().hex[:10]
cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
server=browser=None; dev=None
evidence={'database':name,'cases':[],'viewports':[]}
password='BrowserRole!2026'; reset_password='BrowserReset!2026'


def record(case):
    assert dev.evaluate('document.readyState')=='complete'
    response=next(r for r in reversed(dev.responses) if r['type']=='Document')
    assert response['status']==200,response
    evidence['cases'].append({'case':case,'status':'PASS','path':dev.evaluate('location.pathname'),'http_status':response['status']})


def navigate(path, selector='body'):
    prior=dev.loads
    dev.command('Page.navigate',{'url':'http://127.0.0.1:8027'+path})
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        ready=dev.evaluate('document.readyState === "complete"')
        if dev.loads>prior and ready: break
        time.sleep(.1)
    else: raise AssertionError('Navigation timed out: '+path)
    dev.wait('!!document.querySelector('+json.dumps(selector)+')')
    assert not dev.evaluate('document.title.includes("Server Error")')


def submit(form):
    stamp=dev.evaluate('performance.timeOrigin')
    dev.evaluate('document.querySelector('+json.dumps(form)+').requestSubmit()')
    dev.wait(f'performance.timeOrigin > {stamp} && document.readyState === "complete"',timeout=25)


def login(path,email,pw=password):
    navigate(path,'[name=email]'); dev.fill('[name=email]',email); dev.fill('[name=password]',pw)
    submit('form:has([name=email])')
    assert '/login/' not in dev.evaluate('location.pathname')


def viewport(path,width):
    dev.command('Emulation.setDeviceMetricsOverride',{'width':width,'height':1000,'deviceScaleFactor':1,'mobile':False})
    navigate(path)
    layout=dev.evaluate('({width:innerWidth,body:document.body.scrollWidth,main:!!document.querySelector("main"),forms:document.forms.length})')
    assert layout['main'] and layout['forms']>0
    assert layout['body']<=width+2,layout
    evidence['viewports'].append({'path':path,**layout})


def stop(process):
    if process.poll() is None:
        process.terminate(); process.wait(timeout=15)
        time.sleep(.5)


try:
    env=os.environ.copy(); env['MYSQL_PWD']=db['PASSWORD'] or ''
    with Path('database/crm_db.sql').open('rb') as source:
        subprocess.run([str(Path(settings.MYSQL_BIN)/'mysql.exe'),'--host='+db['HOST'],
            '--port='+str(db['PORT']),'--user='+db['USER'],'--default-character-set=utf8mb4',name],stdin=source,env=env,check=True)
    connection.close(); db['NAME']=name; connection.settings_dict['NAME']=name
    admin=Account.objects.create_superuser('browser-admin@role.test',password,full_name='Browser Admin')
    manager=Account.objects.create_user('browser-manager@role.test',password,role='MANAGER',full_name='Browser Manager')
    with ExitStack() as stack:
        directory=stack.enter_context(tempfile.TemporaryDirectory(prefix='crm_role_browser_',ignore_cleanup_errors=True))
        base=Path(directory)
        module=base/'role_browser_settings.py'
        module.write_text('from config.settings import *\nBASE_DIR=Path('+repr(str(base))+')\nDATABASES["default"]["NAME"]='+repr(name)+'\nALLOWED_HOSTS=["127.0.0.1"]\nLOGGING["handlers"]["database_operations"]["filename"]='+repr(str(OUT/'operations.log'))+'\n',encoding='utf8')
        childenv=os.environ.copy(); childenv['PYTHONPATH']=str(base)+os.pathsep+str(Path.cwd()); childenv['PYTHONIOENCODING']='utf-8'
        with (OUT/'server.log').open('w',encoding='utf8') as log:
            server=subprocess.Popen([str(Path('venv/Scripts/python.exe').resolve()),'manage.py','runserver','127.0.0.1:8027','--noreload','--settings=role_browser_settings'],env=childenv,stdout=log,stderr=log)
            stack.callback(stop,server)
            for _ in range(60):
                try: urllib.request.urlopen('http://127.0.0.1:8027/login/',timeout=1); break
                except Exception: time.sleep(.2)
            profile=base/'edge'
            browser=subprocess.Popen(['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless','--disable-gpu','--no-first-run','--remote-debugging-port=0','--user-data-dir='+str(profile),'--window-size=1440,1000','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            stack.callback(stop,browser)
            for _ in range(80):
                if (profile/'DevToolsActivePort').exists(): break
                time.sleep(.1)
            dev=DevTools(int((profile/'DevToolsActivePort').read_text().splitlines()[0]))
            login('/admin/login/',admin.email); record('ADMIN login and dashboard redirect')
            for width in (1440,390): viewport('/admin/accounts/',width)
            dev.command('Emulation.clearDeviceMetricsOverride')
            navigate('/admin/accounts/')
            dev.click('[data-bs-target="#createModal"]'); dev.wait('document.querySelector("#createModal").classList.contains("show")')
            dev.fill('#createModal [name=email]','browser-created@role.test')
            dev.fill('#createModal [name=role]','CUSTOMER')
            dev.fill('#createModal [name=status]','ACTIVE')
            dev.fill('#createModal [name=full_name]','Browser Created')
            dev.fill('#createModal [name=password]','123')
            dev.fill('#createModal [name=password_confirm]','123')
            submit('#createModal form')
            assert not Account.objects.filter(email='browser-created@role.test').exists()
            assert dev.evaluate('document.querySelectorAll("#createModal .errorlist").length')>0
            dev.fill('#createModal [name=password]',password); dev.fill('#createModal [name=password_confirm]',password)
            submit('#createModal form')
            target=Account.objects.get(email='browser-created@role.test'); assert target.role_code=='CUSTOMER'
            record('ADMIN invalid password validation then create Account')
            navigate(f'/admin/accounts/{target.pk}/'); assert 'Browser Created' in dev.evaluate('document.body.innerText')
            record('ADMIN Account detail')
            navigate('/admin/accounts/?q=browser-created')
            dev.click('[data-role-url]'); dev.wait('document.querySelector("#roleModal").classList.contains("show")')
            dev.fill('#roleForm [name=role]','MANAGER'); submit('#roleForm')
            target.refresh_from_db(); assert target.role_code=='MANAGER'; record('ADMIN role change')
            for action,status in [('lock','LOCKED'),('unlock','ACTIVE')]:
                navigate('/admin/accounts/?q=browser-created')
                dev.click(f'[data-confirm-url="/admin/accounts/{target.pk}/{action}/"]')
                dev.wait('document.querySelector("#confirmModal").classList.contains("show")')
                submit('#confirmForm'); target.refresh_from_db(); assert target.status==status
                record('ADMIN '+action)
            navigate('/admin/accounts/?q=browser-created'); dev.click('[data-reset-url]')
            dev.wait('document.querySelector("#resetModal").classList.contains("show")')
            dev.fill('#resetForm [name=new_password]',reset_password); dev.fill('#resetForm [name=new_password_confirm]',reset_password)
            submit('#resetForm'); target.refresh_from_db(); assert target.check_password(reset_password)
            record('ADMIN password reset')
            navigate('/crm/customers/'); record('ADMIN Customer management')
            navigate('/admin/database/'); submit('form[action="/admin/database/backup/"]')
            assert list((base/'database/backups').glob('*.sql')); record('ADMIN actual Backup UI on clone')
            login('/manager/login/',manager.email); record('MANAGER login and dashboard redirect')
            navigate('/manager/catalog/products/create/','[name=product_name]')
            dev.fill('[name=product_name]','Browser Role Product'); dev.fill('[name=price]','123000')
            for field in ('category','brand'):
                value=dev.evaluate('[...document.querySelector('+json.dumps('[name='+field+']')+').options].find(o=>o.value).value')
                dev.fill('[name='+field+']',value)
            dev.fill('[name=status]','ACTIVE'); submit('form:has([name=product_name])')
            product=Product.objects.get(product_name='Browser Role Product'); assert product.price==123000
            navigate(f'/manager/catalog/products/{product.pk}/edit/','[name=product_name]')
            dev.fill('[name=product_name]','Browser Role Product Edited'); submit('form:has([name=product_name])')
            product.refresh_from_db(); assert product.product_name.endswith('Edited'); record('MANAGER Catalog create and edit')
            navigate('/manager/catalog/products/?q=Browser+Role')
            dev.evaluate('setTimeout(()=>document.querySelector('+json.dumps(f'form[action="/manager/catalog/products/{product.pk}/delete/"]')+').requestSubmit(),50)')
            time.sleep(.2); dev.command('Page.handleJavaScriptDialog',{'accept':True})
            dev.wait('document.readyState === "complete" && !document.body.innerText.includes("Browser Role Product Edited")')
            assert not Product.objects.filter(pk=product.pk).exists(); record('MANAGER Catalog delete disposable product')
            for path in ['/crm/customers/','/crm/feedbacks/','/surveys/manage/','/crm/reports/customers/']:
                navigate(path); record('MANAGER '+path)
            for width in (1440,390): viewport('/crm/customers/',width); viewport('/crm/reports/customers/',width)
            dev.command('Emulation.clearDeviceMetricsOverride')
            navigate('/register/','[name=email]')
            for field,value in {'email':'browser-register@role.test','full_name':'Browser Registered','phone':'0901234567','password':password,'password_confirm':password}.items(): dev.fill('[name='+field+']',value)
            submit('form:has([name=email])')
            customer=Account.objects.get(email='browser-register@role.test'); assert customer.role_code=='CUSTOMER'
            record('CUSTOMER registration default Role')
            if '/login/' in dev.evaluate('location.pathname'): login('/login/',customer.email)
            navigate('/account/profile/','[name=full_name]')
            dev.fill('[name=full_name]','Browser Updated'); submit('form:has([name=full_name])')
            customer.refresh_from_db(); assert customer.full_name=='Browser Updated'; record('CUSTOMER profile update')
            navigate('/account/password/change/','[name=old_password]')
            dev.fill('[name=old_password]',password); dev.fill('[name=new_password1]',reset_password); dev.fill('[name=new_password2]',reset_password)
            submit('form:has([name=old_password])'); customer.refresh_from_db(); assert customer.check_password(reset_password)
            record('CUSTOMER password change retains session')
            for width in (1440,390): viewport('/account/profile/',width)
            dev.command('Emulation.clearDeviceMetricsOverride'); navigate('/products/'); record('CUSTOMER Product catalog')
            cookies=dev.command('Network.getCookies')['cookies']; names={c['name'] for c in cookies}
            assert {'staff_sessionid','manager_sessionid','sessionid','csrftoken'}<=names
            evidence['three_portal_cookies_coexist']=True
            # Deliberate negative browser POST, with JS CSRF refresh bypassed only for this request.
            status=dev.evaluate('fetch("/admin/accounts/",{method:"POST",headers:{"X-CSRFToken":"forged"}}).then(r=>r.status)')
            assert status==403; record('Browser forged CSRF POST rejected')
            remaining={'staff_sessionid','manager_sessionid','sessionid'}
            for action,cookie in [('/admin/logout/','staff_sessionid'),('/manager/logout/','manager_sessionid'),('/logout/','sessionid')]:
                # Render each portal's actual native logout form before submitting.
                navigate('/admin/accounts/' if 'admin/' in action else '/manager/profile/' if 'manager/' in action else '/account/profile/')
                submit('form[action='+json.dumps(action)+']')
                actual={c['name'] for c in dev.command('Network.getCookies')['cookies']}
                remaining.remove(cookie)
                assert cookie not in actual and remaining<=actual
                record('Independent logout '+action)
            login('/login/',customer.email,reset_password); record('CUSTOMER login with changed password')
            # Other portal cookies are absent: a Customer must never reach staff pages.
            navigate('/admin/accounts/'); assert '/login/' in dev.evaluate('location.pathname'); record('CUSTOMER denied ADMIN portal')
            evidence['javascript_errors']=[e for e in dev.errors if e.get('method','').startswith('Runtime.')]
            evidence['console_log_errors']=dev.errors
            evidence['network_failures']=dev.network_failures
            evidence['http_failures']=[r for r in dev.responses if r['status']>=400]
            evidence['document_responses']=[r for r in dev.responses if r['type']=='Document']
            assert not evidence['javascript_errors'], evidence['javascript_errors']
            assert not evidence['network_failures'],evidence['network_failures']
            assert len(evidence['http_failures'])==1 and evidence['http_failures'][0]['status']==403
            evidence['expected_negative_http']='One intentional forged-CSRF Fetch returns 403 and produces a browser network console entry.'
except Exception:
    import traceback
    evidence['error']=traceback.format_exc()
    raise
finally:
    if dev:
        evidence['console_log_errors']=dev.errors
        evidence['network_failures']=dev.network_failures
        try: evidence['last_path']=dev.evaluate('location.pathname'); dev.sock.close()
        except Exception: pass
    if browser: stop(browser)
    if server: stop(server)
    connection.close(); db['NAME']=original; connection.settings_dict['NAME']=original
    cursor.execute(f'DROP DATABASE `{name}`')
    evidence['source_unchanged']=database_fingerprint(root)==before
    cursor.close(); root.close()
    (OUT/'results.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    assert evidence['source_unchanged']
    print(json.dumps({'cases':len(evidence['cases']),'source_unchanged':evidence['source_unchanged'],'error':evidence.get('error')},indent=2))
