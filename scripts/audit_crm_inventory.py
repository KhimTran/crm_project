"""Read-only database integrity and runtime diagnostics for the audit."""
import os,json
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.db import connection
from apps.customers.reports import favorite_brand_report
result={}
with connection.cursor() as c:
    c.execute('SELECT VERSION(),DATABASE()'); result['runtime']=c.fetchone()
    c.execute('SHOW TABLES'); tables=[r[0] for r in c.fetchall()]
    result['counts']={}
    for table in tables:
        c.execute('SELECT COUNT(*) FROM `'+table.replace('`','``')+'`'); result['counts'][table]=c.fetchone()[0]
    c.execute('SELECT TABLE_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL')
    result['foreign_keys']=[]
    for table,column,target,key in c.fetchall():
        c.execute(f'SELECT COUNT(*) FROM `{table}` s LEFT JOIN `{target}` t ON s.`{column}`=t.`{key}` WHERE s.`{column}` IS NOT NULL AND t.`{key}` IS NULL')
        result['foreign_keys'].append({'source':table+'.'+column,'target':target+'.'+key,'orphans':c.fetchone()[0]})
    c.execute("SELECT COUNT(*) FROM survey_answers a JOIN survey_questions q ON q.question_id=a.question_id JOIN survey_responses r ON r.response_id=a.response_id JOIN survey_recipients rc ON rc.recipient_id=r.recipient_id LEFT JOIN survey_options o ON o.option_id=a.option_id WHERE q.survey_id<>rc.survey_id OR (a.option_id IS NOT NULL AND (o.option_id IS NULL OR o.question_id<>q.question_id))")
    result['invalid_answer_relationships']=c.fetchone()[0]
    c.execute('SELECT survey_id,audience FROM surveys ORDER BY survey_id'); result['survey_audience_presence']=[{'id':r[0],'configured':bool(json.loads(r[1]) if isinstance(r[1],str) else r[1])} for r in c.fetchall()]
result['favorite_brands']=favorite_brand_report()
Path('docs/crm_audit_20261101/database_inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print('Tables',len(tables),'FK orphans',sum(r['orphans'] for r in result['foreign_keys']),'invalid survey relationships',result['invalid_answer_relationships'])
