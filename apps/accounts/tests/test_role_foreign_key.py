from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError

from apps.accounts.models import Account, Role
from apps.accounts.selectors import account_data
from apps.accounts.testing import PortalTestCase


class RoleForeignKeyTests(PortalTestCase):
    password = 'StrongPass!2026'

    def test_real_relation_and_string_contract_for_each_role(self):
        for code in ('ADMIN', 'MANAGER', 'CUSTOMER'):
            with self.subTest(code=code):
                account = Account.objects.create_user(code+'@role.test', self.password, role=code)
                account.refresh_from_db()
                self.assertIsInstance(account.role, Role)
                self.assertIsInstance(account.role_id, int)
                self.assertEqual(account.role.role_code, code)
                self.assertEqual(account_data(account)['role'], code)
                self.assertEqual(account_data(account)['profile']['type'], code)
                self.assertTrue(Account.objects.filter(role__role_code=code, pk=account.pk).exists())
                self.assertTrue(account.check_password(self.password))

    def test_mapping_uses_code_instead_of_fixed_ids(self):
        Role.objects.all().delete()
        for index, code in enumerate(('CUSTOMER', 'ADMIN', 'MANAGER'), start=101):
            Role.objects.create(role_id=index, role_code=code, role_name=code)
        account = Account.objects.create_user('mapping@role.test', self.password, role='MANAGER')
        self.assertEqual(account.role_id, Role.objects.get(role_code='MANAGER').pk)
        self.assertEqual(account.role_code, 'MANAGER')

    def test_referenced_role_cannot_be_deleted_by_orm_or_sql(self):
        account = Account.objects.create_user('protected@role.test', self.password)
        with self.assertRaises(ProtectedError):
            account.role.delete()
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM roles WHERE role_id=%s', [account.role_id])

    def test_database_rejects_orphan_null_and_extra_role(self):
        account = Account.objects.create_user('integrity@role.test', self.password)
        for value in (None, -1):
            with self.subTest(value=value), self.assertRaises(IntegrityError), transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE accounts SET role_id=%s WHERE account_id=%s', [value, account.pk])
        with self.assertRaises(IntegrityError), transaction.atomic():
            Role.objects.create(role_code='ROOT', role_name='Invalid')
        with self.assertRaises(ValidationError):
            Account.objects.create_user('invalid@role.test', self.password, role='ROOT')

    def test_single_unique_code_index_and_no_legacy_column(self):
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(cursor, 'roles')
            columns = connection.introspection.get_table_description(cursor, 'accounts')
        self.assertEqual(sum(c['unique'] and c['columns']==['role_code'] for c in constraints.values()), 1)
        self.assertNotIn('role', [c.name for c in columns])
        self.assertIn('role_id', [c.name for c in columns])
