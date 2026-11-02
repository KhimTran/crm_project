"""Read-only Manager Survey filter layout checks in headless Edge."""
import os,json,subprocess,tempfile,re
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.test import RequestFactory
from apps.accounts.models import Account
from apps.surveys.views import manage_list

edge=Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
user=Account.objects.filter(role='MANAGER',status='ACTIVE').first()
probe='''<script>window.addEventListener('load',()=>setTimeout(()=>{const f=document.querySelector('.survey-list-filter');const rect=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,height:r.height}};const pre=document.createElement('pre');pre.id='layout-result';pre.textContent=JSON.stringify({controls:[...f.querySelectorAll('input,select,.btn')].map(rect),form:rect(f)});document.body.append(pre)},200));</script>'''
with tempfile.TemporaryDirectory(prefix='survey_filter_layout_') as directory:
    root=Path(directory); signatures={}
    for status in ['', 'DRAFT', 'ACTIVE', 'CLOSED']:
        request=RequestFactory().get('/surveys/manage/',{'status':status,'q':'','date_from':'2026-10-01','date_to':'2026-12-31'})
        request.user=user
        # Layout verification must not run the existing expiry maintenance action.
        with patch('apps.surveys.views.close_expired'):
            response=manage_list(request)
        assert response.status_code==200
        html=response.content.decode().replace('href="/static/','href="http://127.0.0.1:8000/static/')+probe
        page=root/'page.html'; page.write_text(html,encoding='utf-8')
        for width in [1440,1280,1200,1024,390]:
            result=subprocess.run([str(edge),'--headless','--disable-gpu','--no-first-run','--hide-scrollbars',f'--user-data-dir={root / "browser"}',f'--window-size={width},1000','--virtual-time-budget=3500','--dump-dom',page.as_uri()],capture_output=True,timeout=35)
            match=re.search(r'<pre id="layout-result">(.*?)</pre>',result.stdout.decode('utf-8',errors='replace'))
            assert match, result.stderr.decode(errors='replace')[-300:]
            data=json.loads(match[1]); controls=data['controls']
            assert len(controls)==6
            assert all(c['right']<=data['form']['right']+1 for c in controls),data
            assert abs(controls[-1]['y']-controls[-2]['y'])<1,data
            assert all(abs(c['height']-42)<1 for c in controls),data
            if width>=1200: assert max(c['y'] for c in controls)-min(c['y'] for c in controls)<1,data
            if width in signatures: assert signatures[width]==data,'Layout changed with status'
            signatures[width]=data
            print('Manager Surveys',status or 'ALL',width,'PASS')
