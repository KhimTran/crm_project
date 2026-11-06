from io import StringIO
from django.contrib.auth import authenticate
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.accounts.managers import resolve_account_role
from apps.accounts.models import Account, Role
from apps.accounts.selectors import list_account_page
from apps.accounts.testing import PortalTestCase
from apps.customers.selectors import customer_queryset


class RoleHardeningTests(PortalTestCase):
    password = 'HardeningStrong!2026'

    def test_runtime_resolution_is_read_only_and_missing_role_is_controlled(self):
        Role.objects.filter(role_code='CUSTOMER').delete()
        with CaptureQueriesContext(connection) as queries:
            with self.assertRaises(ValidationError):
                resolve_account_role(' customer ')
        self.assertFalse(Role.objects.filter(role_code='CUSTOMER').exists())
        self.assertTrue(queries)
        self.assertTrue(all(q['sql'].lstrip().upper().startswith('SELECT') for q in queries))
        with self.assertRaises(ValidationError):
            Account.objects.create_user('missing@role.test', self.password)
        self.assertFalse(Account.objects.filter(email='missing@role.test').exists())

    def test_default_is_initialized_only_for_new_accounts(self):
        account = Account(email='default@role.test')
        self.assertEqual(account.role_id, Role.objects.get(role_code='CUSTOMER').pk)
        self.assertEqual(account.role_code, 'CUSTOMER')
        account.set_password(self.password); account.save()
        account.role_id = None
        with self.assertRaises(ValidationError):
            _ = account.role_code
        with self.assertRaises(ValidationError):
            account.save()
        account.refresh_from_db()
        self.assertEqual(account.role_code, 'CUSTOMER')

    def test_explicit_missing_or_orphan_role_is_not_defaulted(self):
        for value in (None, -1):
            account = Account(email='invalid@role.test', role_id=value)
            with self.subTest(value=value), self.assertRaises(ValidationError):
                _ = account.role_code

    def test_explicit_initializer_is_idempotent_and_preserves_existing_labels(self):
        Role.objects.filter(role_code='MANAGER').delete()
        Role.objects.filter(role_code='ADMIN').update(role_name='Existing label')
        call_command('initialize_roles',stdout=StringIO())
        before=list(Role.objects.order_by('pk').values())
        call_command('initialize_roles',stdout=StringIO())
        self.assertEqual(list(Role.objects.order_by('pk').values()),before)
        self.assertEqual(Role.objects.get(role_code='ADMIN').role_name,'Existing label')
        account=Account.objects.create_superuser('initialized@role.test',self.password)
        self.assertTrue(account.is_superuser)

    def test_account_list_queries_do_not_grow_per_row(self):
        actor=Account.objects.create_superuser('list-admin@role.test',self.password)
        for index in range(8):
            Account.objects.create_user(f'list-{index}@role.test',self.password)
        with CaptureQueriesContext(connection) as small:
            list_account_page(actor,page_size=1)
        with CaptureQueriesContext(connection) as large:
            list_account_page(actor,page_size=20)
        self.assertEqual(len(small),len(large))

    def test_customer_list_does_not_fetch_roles_per_row(self):
        for index in range(4):
            Account.objects.create_user(f'customer-{index}@role.test',self.password)
        with self.assertNumQueries(1):
            self.assertEqual([a.role_code for a in customer_queryset()],['CUSTOMER']*4)

    def test_authentication_and_session_reload_join_fresh_role(self):
        account=Account.objects.create_user('auth@role.test',self.password,role='MANAGER')
        with self.assertNumQueries(1):
            current=authenticate(email=account.email,password=self.password)
            self.assertEqual(current.role_code,'MANAGER')
        Account.objects.filter(pk=account.pk).update(role='CUSTOMER')
        with self.assertNumQueries(1):
            current=ModelBackend().get_user(account.pk)
            self.assertEqual(current.role_code,'CUSTOMER')
            self.assertFalse(current.is_staff)
        Account.objects.filter(pk=account.pk).update(status='LOCKED')
        self.assertIsNone(ModelBackend().get_user(account.pk))
