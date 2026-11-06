"""Read-only verification against preflight.json; never print account data or hashes."""
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
from apps.admin_portal.services.restore_service import database_fingerprint


def verify(baseline):
    connection.ensure_connection()
    before = baseline['fingerprints']
    after = database_fingerprint(connection.connection)
    assert set(before) == set(after), 'Unexpected table changes'
    for table, value in before.items():
        if table not in ('accounts', 'roles', 'django_migrations'):
            assert list(after[table]) == value, 'Data changed in '+table
    with connection.cursor() as cursor:
        columns = before['accounts'][0]
        fields = ','.join('r.role_code' if col == 'role' else 'a.`'+col+'`' for col in columns)
        cursor.execute('SELECT '+fields+' FROM accounts a JOIN roles r ON a.role_id=r.role_id')
        rows = sorted(repr(tuple(row)) for row in cursor.fetchall())
        assert len(rows) == before['accounts'][1], 'Account count changed'
        assert hashlib.sha256('\n'.join(rows).encode()).hexdigest() == before['accounts'][2], 'Account values changed'
        cursor.execute('SELECT r.role_code,COUNT(*) FROM accounts a JOIN roles r ON a.role_id=r.role_id GROUP BY r.role_code')
        mapping = dict(cursor.fetchall())
        cursor.execute('SELECT role_code,role_name FROM roles')
        assert dict(cursor.fetchall()) == {'ADMIN': 'Quản trị viên', 'MANAGER': 'Quản lý', 'CUSTOMER': 'Khách hàng'}, 'Role labels differ'
        cursor.execute('SELECT role_id,role_code,description,created_at,updated_at FROM roles')
        assert sorted(repr(tuple(row)) for row in cursor.fetchall()) == baseline['role_reference'], 'Other Role values changed'
        constraints = connection.introspection.get_constraints(cursor, 'accounts')
        assert any(c['foreign_key'] == ('roles', 'role_id') and c['columns'] == ['role_id'] for c in constraints.values()), 'Missing role FK'
        cursor.execute('SELECT TABLE_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE CONSTRAINT_SCHEMA=DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL')
        fks = cursor.fetchall()
        for source, column, target, key in fks:
            # Identifiers are database metadata, escaped independently.
            quote = lambda name: '`'+name.replace('`','``')+'`'
            cursor.execute('SELECT COUNT(*) FROM '+quote(source)+' s LEFT JOIN '+quote(target)+' t ON s.'+quote(column)+'=t.'+quote(key)+' WHERE s.'+quote(column)+' IS NOT NULL AND t.'+quote(key)+' IS NULL')
            assert cursor.fetchone()[0] == 0, 'Orphan records in '+source
    assert after['django_migrations'][1] == before['django_migrations'][1]+3, 'Migration history count differs'
    return {'database': connection.settings_dict['NAME'], 'accounts_preserved': len(rows),
            'mapping': mapping, 'tables': len(after), 'foreign_keys_checked': len(fks),
            'all_account_and_unrelated_values_preserved': True,
            'role_names_normalized': True, 'orphan_records': 0}


if __name__ == '__main__':
    result = verify(json.loads(Path(sys.argv[1]).read_text(encoding='utf8')))
    print(json.dumps(result, indent=2))
