"""Real Edge forms/JavaScript/CSRF/SQL audit on a disposable MySQL clone."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request
from contextlib import ExitStack
from uuid import uuid4

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.db import connection
from apps.accounts.models import Account
from apps.surveys.models import Survey, SurveyQuestion, SurveyOption, SurveyRecipient, SurveyAnswer
from apps.admin_portal.services.restore_service import database_fingerprint
from browser_cdp import DevTools

OUT = Path(os.environ.get('CRM_AUDIT_OUT','docs/crm_audit_20261101/completion')).resolve()
OUT.mkdir(parents=True, exist_ok=True)
db = settings.DATABASES['default']; original = db['NAME']
root = connection.Database.connect(**connection.get_connection_params())
before = database_fingerprint(root)
name = 'crm_browser_audit_'+uuid4().hex[:10]
cursor = root.cursor()
cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
env = os.environ.copy(); env['MYSQL_PWD'] = db['PASSWORD']
server = browser = None
evidence = {'cases': [], 'database': name}
try:
    with Path('database/crm_db.sql').open('rb') as source:
        subprocess.run(['mysql.exe', '--host='+db['HOST'], '--port='+str(db['PORT']), '--user='+db['USER'], '--default-character-set=utf8mb4', name], stdin=source, env=env, check=True)
    connection.close(); db['NAME'] = name; connection.settings_dict['NAME'] = name
    password = 'BrowserAudit!2026'
    manager = Account.objects.create_user('browser-manager@audit.test', password, role='MANAGER')
    customer = Account.objects.create_user('browser-customer@audit.test', password, full_name='Browser Customer')
    with ExitStack() as stack:
        directory = stack.enter_context(tempfile.TemporaryDirectory(prefix='crm_browser_'))
        base = Path(directory)
        (base/'crm_browser_settings.py').write_text('from config.settings import *\nDATABASES["default"]["NAME"]='+repr(name)+'\nALLOWED_HOSTS=["127.0.0.1"]\nLOGGING["handlers"]["database_operations"]["filename"]='+repr(str(OUT/'browser_operations.log'))+'\n', encoding='utf-8')
        env = os.environ.copy(); env['PYTHONPATH'] = str(base)+os.pathsep+str(Path.cwd()); env['PYTHONIOENCODING'] = 'utf-8'
        with (OUT/'browser_server.log').open('w', encoding='utf-8') as log:
            server = subprocess.Popen([str(Path('venv/Scripts/python.exe').resolve()), 'manage.py', 'runserver', '127.0.0.1:8019', '--noreload', '--settings=crm_browser_settings'], env=env, stdout=log, stderr=log)
            stack.callback(lambda: (server.terminate(), server.wait(timeout=15)))
            for _ in range(60):
                try:
                    urllib.request.urlopen('http://127.0.0.1:8019/login/', timeout=1); break
                except Exception:
                    time.sleep(.2)
            profile = base/'edge'
            browser = subprocess.Popen(['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', '--headless', '--disable-gpu', '--no-first-run', '--remote-debugging-port=0', '--user-data-dir='+str(profile), '--window-size=1440,1000', 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            stack.callback(lambda: (browser.terminate(), browser.wait(timeout=15), time.sleep(.5)))
            for _ in range(80):
                if (profile/'DevToolsActivePort').exists(): break
                time.sleep(.1)
            dev = DevTools(int((profile/'DevToolsActivePort').read_text().splitlines()[0]))
            origin = 'http://127.0.0.1:8019'
            def navigate(path, selector):
                dev.navigate(origin+path); dev.wait(f'!!document.querySelector({json.dumps(selector)})')
            def login(email, destination):
                navigate('/login/', 'input[name=email]')
                dev.fill('input[name=email]', email); dev.fill('input[name=password]', password)
                dev.click('.customer-auth-card button[type=submit]'); dev.wait(f'location.pathname.startsWith({json.dumps(destination)}) && document.readyState === "complete"')
            login(manager.email, '/manager/')
            navigate('/surveys/manage/new/', '#sv-cb-add')
            dev.fill('[name=title]', 'BROWSER survey builder')
            dev.fill('[name=objective]', 'SATISFACTION')
            today = __import__('datetime').date.today()
            dev.fill('[name=start_at]', today.isoformat())
            dev.fill('[name=end_at]', (today+__import__('datetime').timedelta(days=7)).isoformat())
            dev.click('[name=audience][value=pick]')
            dev.click(f'[name=customer_ids][value="{customer.pk}"]')
            # Add and configure actual builder cards through their input listeners.
            for index, kind in enumerate(['SINGLE_CHOICE', 'MULTI_CHOICE', 'RATING', 'TEXT']):
                if index or not dev.evaluate('!!document.querySelector(".sv-cb-q.is-open")'):
                    dev.click('#sv-cb-add')
                dev.fill('.sv-cb-q.is-open .sv-cb-type select', kind)
                dev.fill('.sv-cb-q.is-open [data-focus=text]', 'Browser '+kind)
                if kind in ('SINGLE_CHOICE', 'MULTI_CHOICE'):
                    dev.fill('.sv-cb-q.is-open [data-focus=opt-0]', 'Yonex')
                    dev.fill('.sv-cb-q.is-open [data-focus=opt-1]', 'Victor')
                elif kind == 'RATING':
                    dev.fill('.sv-cb-q.is-open [id^=sv-cb-rating_max]', '10')
            assert dev.evaluate('document.querySelector("#sv-cb-json").value')
            dev.click('[data-action=save]')
            dev.wait('!location.pathname.endsWith("/new/") && document.readyState === "complete"')
            survey = Survey.objects.get(title='BROWSER survey builder')
            questions = list(survey.surveyquestion_set.order_by('sort_order'))
            assert [q.question_type for q in questions] == ['SINGLE_CHOICE','MULTI_CHOICE','RATING','TEXT']
            assert survey.audience['audience'] == 'pick', survey.audience
            evidence['cases'].append({'case': 'Browser Create + Draft + 4 answer types + saved audience', 'status': 'PASS', 'survey_id': survey.pk, 'question_ids': [q.pk for q in questions]})
            navigate(f'/surveys/manage/{survey.pk}/edit/', '#sv-cb-add')
            # Keyboard reorder is a supported accessible user interaction.
            dev.evaluate('document.querySelectorAll(".sv-cb-handle")[3].dispatchEvent(new KeyboardEvent("keydown", {key:"ArrowUp",bubbles:true}))')
            dev.click('.sv-cb-q-toggle')
            dev.fill('.sv-cb-q.is-open [data-focus=text]', 'Browser single edited')
            dev.click('#sv-cb-add')
            dev.fill('.sv-cb-q.is-open [data-focus=text]', 'Disposable question')
            dev.click('.sv-cb-q.is-open details summary')
            # Accept the real native confirmation dialog using CDP, no confirm stub.
            dev.evaluate('setTimeout(()=>document.querySelector(".sv-cb-q.is-open .sv-cb-menu-item.is-danger").click(),50)')
            time.sleep(.2); dev.command('Page.handleJavaScriptDialog', {'accept': True})
            previous_origin = dev.evaluate('performance.timeOrigin')
            dev.click('[data-action=save]')
            dev.wait(f'performance.timeOrigin > {previous_origin} && document.readyState === "complete"')
            actual = list(survey.surveyquestion_set.order_by('sort_order').values_list('question_type','question_text'))
            assert [r[0] for r in actual] == ['SINGLE_CHOICE','MULTI_CHOICE','TEXT','RATING'], actual
            assert actual[0][1] == 'Browser single edited' and len(actual) == 4
            evidence['cases'].append({'case':'Browser Edit / reorder / add / delete / persisted SQL order','status':'PASS','questions':actual})
            navigate(f'/surveys/manage/{survey.pk}/audience/', 'button[name=action]')
            assert not dev.evaluate('!!document.querySelector("[name=audience], [name=customer_ids]")')
            evidence['send_confirmation'] = dev.evaluate('document.body.innerText')
            assert not dev.evaluate('document.querySelector("button[name=action]").disabled'), evidence['send_confirmation']
            dev.click('button[name=action]')
            dev.wait(f'location.pathname === "/surveys/manage/{survey.pk}/" && document.readyState === "complete"')
            recipient = SurveyRecipient.objects.get(survey=survey, customer=customer)
            assert SurveyRecipient.objects.filter(survey=survey).count() == 1
            evidence['cases'].append({'case':'Browser Send uses saved pick audience without second selection','status':'PASS','recipient_id':recipient.pk})
            # Existing MATRIX type remains supported for historical/versioned questionnaires.
            matrix = SurveyQuestion.objects.create(survey=survey, question_text='Browser matrix service', question_type='MATRIX', is_required=True, sort_order=5)
            SurveyOption.objects.create(question=matrix, option_text='Stringing service', sort_order=1)
            login(customer.email, '/')
            from apps.feedback.models import Feedback
            from apps.catalog.models import Product
            product = Product.objects.filter(status='ACTIVE').first()
            navigate('/feedbacks/new/', '[name=content]')
            dev.fill('[name=product]', str(product.pk))
            dev.click('[name=rating][value="5"]')
            dev.fill('[name=content]', 'BROWSER two-status feedback')
            dev.click('form.cf-form button[type=submit]')
            dev.wait('location.pathname === "/feedbacks/mine/" && document.readyState === "complete"')
            feedback = Feedback.objects.get(customer=customer, content='BROWSER two-status feedback')
            assert feedback.status == 'NEW' and feedback.resolved_at is None
            navigate(f'/crm/feedbacks/{feedback.pk}/', '[name=manager_note]')
            assert dev.evaluate('[...document.querySelector("[name=status]").options].map(x=>x.value)') == ['NEW','RESOLVED']
            feedback.refresh_from_db(); assert feedback.status == 'NEW'
            dev.fill('[name=status]', 'RESOLVED')
            dev.fill('[name=manager_note]', 'Browser resolved directly')
            previous_origin = dev.evaluate('performance.timeOrigin')
            dev.click('form.crm-form button[type=submit]')
            dev.wait(f'performance.timeOrigin > {previous_origin} && document.readyState === "complete"')
            feedback.refresh_from_db()
            assert feedback.status == 'RESOLVED' and feedback.handled_by_id == manager.pk and feedback.resolved_at
            navigate('/feedbacks/mine/', 'body')
            assert 'Browser resolved directly' in dev.evaluate('document.body.innerText')
            evidence['cases'].append({'case':'Browser Customer creates NEW / Manager reads without mutation / direct resolve / Customer history', 'status':'PASS','feedback_id':feedback.pk})
            navigate('/surveys/mine/', 'body')
            dev.wait('!!document.querySelector('+json.dumps(f'a[href="/surveys/recipients/{recipient.pk}/"]')+')')
            evidence['cases'].append({'case':'Customer invitation list links to the correct saved recipient','status':'PASS'})
            navigate(f'/surveys/recipients/{recipient.pk}/', '#sv-form')
            for kind in ('SINGLE_CHOICE','MULTI_CHOICE','RATING'):
                dev.click(f'[data-type="{kind}"] input')
            dev.click('[data-type=SINGLE_CHOICE] label:nth-of-type(2) input')
            dev.click('[data-type=MULTI_CHOICE] label:nth-of-type(2) input')
            dev.click('[data-type=RATING] input[value="10"]')
            assert dev.evaluate('document.querySelectorAll("[data-type=SINGLE_CHOICE] input:checked").length') == 1
            assert dev.evaluate('document.querySelectorAll("[data-type=MULTI_CHOICE] input:checked").length') == 2
            dev.fill('[data-type=TEXT] textarea', 'Browser customer feedback')
            dev.fill('[data-type=MATRIX] select', '5')
            dev.evaluate('setTimeout(()=>document.querySelector("#sv-form button[type=submit]").click(),50)')
            time.sleep(.2); dev.command('Page.handleJavaScriptDialog', {'accept': True})
            dev.wait('location.pathname.endsWith("/result/") && document.readyState === "complete"')
            assert SurveyAnswer.objects.filter(response__recipient=recipient).count() == 6
            assert SurveyAnswer.objects.get(response__recipient=recipient, question__question_type='RATING').rating_value == 10
            evidence['cases'].append({'case':'Browser customer submit Single/Multi/Text/Rating/Matrix through survey_take.js','status':'PASS','answer_count':6,'rating':10})
            navigate(f'/surveys/manage/{survey.pk}/stats/', 'body')
            assert 'Browser' in dev.evaluate('document.body.innerText')
            navigate('/surveys/manage/results/', 'body')
            from apps.surveys.survey_report import build_report
            expected_responses=build_report()['total']['count']
            assert expected_responses>0
            dev.wait('!!document.querySelector(".report-tile strong") && document.querySelector(".report-tile strong").textContent.trim().startsWith('+json.dumps(str(expected_responses))+')')
            assert str(survey.pk) not in dev.evaluate('[...document.querySelector("#report-survey").options].map(o=>o.value)')
            evidence['cases'].append({'case':'Manager specialized Survey Results matches published 8-question responses and excludes custom questionnaire','status':'PASS','responses':expected_responses})
            # Capture at both desktop and mobile dimensions without changing data.
            for width in (1440,390):
                dev.command('Emulation.setDeviceMetricsOverride', {'width':width,'height':1000,'deviceScaleFactor':1,'mobile':False})
                dev.navigate(origin+'/crm/reports/customers/'); dev.wait('document.readyState === "complete"')
                dev.wait('typeof Chart !== "undefined" && Object.keys(Chart.instances).length === 5')
            evidence['report_chart_count'] = dev.evaluate('Object.keys(Chart.instances).length')
            evidence['browser_errors'] = dev.errors
            evidence['network_failures'] = dev.network_failures
            evidence['http_failures'] = [r for r in dev.responses if r['status']>=400]
            assert not dev.errors, dev.errors
            assert not evidence['network_failures'],evidence['network_failures']
            assert not evidence['http_failures'],evidence['http_failures']
            evidence['cases'].append({'case':'Browser console/uncaught errors during builder/send/take/stats/report','status':'PASS'})
            dev.sock.close()
except Exception as exc:
    import traceback
    evidence['error'] = traceback.format_exc()
    if 'dev' in globals():
        try:
            evidence['page'] = dev.evaluate('document.body.innerText')
            evidence['browser_errors'] = dev.errors
        except Exception:
            pass
    raise
finally:
    if browser:
        browser.terminate(); browser.wait(timeout=15)
    if server:
        server.terminate(); server.wait(timeout=15)
    connection.close(); db['NAME'] = original; connection.settings_dict['NAME'] = original
    cursor.execute(f'DROP DATABASE `{name}`')
    evidence['live_database_unchanged'] = database_fingerprint(root) == before
    cursor.close(); root.close()
    (OUT/'browser_survey.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    assert evidence['live_database_unchanged']
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
