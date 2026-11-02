"""Read-only rendering and headless Edge layout checks on local demo data."""
import os,json,subprocess,tempfile,re
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.test import RequestFactory
from apps.accounts.models import Account
from apps.feedback.views import feedback_list
from apps.accounts.views import account_list
from apps.customers.views import customer_list
from apps.catalog.views import brand_list, category_list

for role, views in [('ADMIN', [account_list, customer_list, feedback_list]),
                    ('MANAGER', [customer_list, brand_list, category_list, feedback_list])]:
    actor = Account.objects.filter(role=role, status='ACTIVE').first()
    for view in views:
        for params in [{}, {'page': 2}, {'q': 'Demo'}]:
            request = RequestFactory().get('/crm/', params)
            request.user = actor
            assert view(request).status_code == 200, (role, view.__name__, params)
    print(role, 'list/search/page render PASS')

edge=Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
probe='''<script>window.addEventListener('load',()=>{setTimeout(()=>{const f=document.querySelector('.crm-feedback-filter');const fields=[...f.children];const buttons=[...f.querySelectorAll('.crm-actions .crm-btn')];const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,right:r.right}};const data={fields:fields.map(e=>rect(e.querySelector("input,select")||e)),buttons:buttons.map(rect),form:rect(f),viewport:innerWidth};const pre=document.createElement('pre');pre.id='layout-result';pre.textContent=JSON.stringify(data);document.body.append(pre)},200)});</script>'''
with tempfile.TemporaryDirectory(prefix='crm_feedback_layout_') as directory:
    root=Path(directory)
    signatures = {}
    for role in ['MANAGER','ADMIN']:
        user=Account.objects.filter(role=role,status='ACTIVE').first()
        for status in ['NEW','RESOLVED']:
            request=RequestFactory().get('/crm/feedbacks/',{'status':status}); request.user=user
            response=feedback_list(request)
            assert response.status_code==200
            html=response.content.decode().replace('href="/static/','href="'+Path('static').resolve().as_uri()+'/')+probe
            page=root/'page.html'; page.write_text(html,encoding='utf-8')
            for width in [1440,1024,390]:
                result=subprocess.run([str(edge),'--headless','--disable-gpu','--no-first-run','--disable-extensions','--hide-scrollbars','--allow-file-access-from-files',f'--user-data-dir={root / "browser"}',f'--window-size={width},1000','--virtual-time-budget=3500','--dump-dom',page.as_uri()],capture_output=True,timeout=35)
                text=result.stdout.decode('utf-8',errors='replace')
                match=re.search(r'<pre id="layout-result">(.*?)</pre>',text)
                assert match, result.stderr.decode(errors='replace')[-300:]
                data=json.loads(match[1]); buttons=data['buttons']; fields=data['fields']
                assert abs(buttons[0]['y']-buttons[1]['y'])<2, data
                assert all(x['right']<=data['form']['right']+1 for x in fields+buttons), data
                if width==1440:
                    assert max(x['y'] for x in fields)-min(x['y'] for x in fields)<2, data
                signature = (fields, buttons, data['form'])
                key = (role, width)
                if key in signatures:
                    assert signatures[key] == signature, 'Layout changed with status'
                signatures[key] = signature
                print(role,status,width,'PASS')
