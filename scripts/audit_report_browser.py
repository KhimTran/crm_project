"""Read-only customer report chart rendering and browser error capture."""
import os,json,re,subprocess,tempfile
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.test import RequestFactory
from apps.accounts.models import Account
from apps.customers.views import customer_report
request=RequestFactory().get('/crm/reports/customers/'); request.user=Account.objects.filter(role='MANAGER',status='ACTIVE').first()
page=customer_report(request).content.decode().replace('href="/static/','href="http://127.0.0.1:8000/static/').replace('src="/static/','src="http://127.0.0.1:8000/static/')
early='''<script>window.auditErrors=[];addEventListener('error',e=>auditErrors.push(e.message||e.target.src||e.target.href||'resource error'),true);addEventListener('unhandledrejection',e=>auditErrors.push(String(e.reason)));</script>'''
probe='''<script>addEventListener('load',()=>setTimeout(()=>{let canvases=[...document.querySelectorAll('canvas')];let data={errors:auditErrors,chartLibrary:typeof Chart,canvases:canvases.length,rendered:typeof Chart==='function'?canvases.filter(c=>Chart.getChart(c)).length:0};let pre=document.createElement('pre');pre.id='audit-result';pre.textContent=JSON.stringify(data);document.body.append(pre)},500));</script>'''
page=page.replace('<head>','<head>'+early)+probe
results=[]
with tempfile.TemporaryDirectory(prefix='crm_report_browser_') as folder:
    root=Path(folder); html=root/'report.html'; html.write_text(page,encoding='utf-8')
    for width in [1440,390]:
        result=subprocess.run(['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','--headless','--disable-gpu','--no-first-run',f'--user-data-dir={root/"browser"}',f'--window-size={width},1000','--virtual-time-budget=5000','--dump-dom',html.as_uri()],capture_output=True,timeout=40)
        found=re.search(r'<pre id="audit-result">(.*?)</pre>',result.stdout.decode('utf-8',errors='replace'))
        row={'width':width,**json.loads(found[1])} if found else {'width':width,'error':'No browser probe output'}
        results.append(row); print(row)
Path('docs/crm_audit_20261101/report_browser.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
