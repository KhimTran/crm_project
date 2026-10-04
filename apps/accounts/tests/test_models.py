from django.contrib.auth import authenticate, get_user, get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import RequestFactory, TestCase

from apps.accounts.constants import AccountRole, AccountStatus


class AccountFoundationTests(TestCase):
    password = "StrongPass!2026"

    def test_customer_creation_normalizes_email_and_hashes_password(self):
        account = get_user_model().objects.create_user("  Customer@Example.COM  ", self.password)
        self.assertEqual(account.email, "customer@example.com")
        self.assertEqual(account.role, AccountRole.CUSTOMER)
        self.assertEqual(account.status, AccountStatus.ACTIVE)
        self.assertNotEqual(account.password, self.password)
        self.assertTrue(account.check_password(self.password))
        self.assertFalse(account.check_password("wrong-password"))
        self.assertTrue(account.is_active)
        self.assertFalse(account.is_staff)
        self.assertFalse(account.is_superuser)

    def test_admin_creation_has_framework_permissions(self):
        account = get_user_model().objects.create_superuser("Admin@Example.COM", self.password)
        self.assertEqual(account.role, AccountRole.ADMIN)
        self.assertEqual(account.status, AccountStatus.ACTIVE)
        self.assertTrue(account.is_staff)
        self.assertTrue(account.is_superuser)
        self.assertTrue(account.has_perm("accounts.change_account"))
        group = Group.objects.create(name="Account operators")
        account.groups.add(group)
        self.assertTrue(account.groups.filter(pk=group.pk).exists())

    def test_duplicate_email_is_rejected_after_normalization(self):
        get_user_model().objects.create_user("member@example.com", self.password)
        with self.assertRaises(ValidationError):
            get_user_model().objects.create_user(" MEMBER@example.com ", self.password)

    def test_role_and_status_choices_are_enforced(self):
        model = get_user_model()
        admin = model.objects.create_user("role@example.com", self.password, role=AccountRole.ADMIN)
        self.assertEqual(admin.role, AccountRole.ADMIN)
        locked = model.objects.create_user("locked@example.com", self.password, status=AccountStatus.LOCKED)
        self.assertEqual(locked.status, AccountStatus.LOCKED)
        self.assertFalse(locked.is_active)
        self.assertFalse(locked.is_staff)
        self.assertFalse(locked.is_superuser)
        with self.assertRaises(ValidationError):
            model.objects.create_user("bad-role@example.com", self.password, role="OTHER")
        with self.assertRaises(ValidationError):
            model.objects.create_user("bad-status@example.com", self.password, status="OTHER")

    def test_role_status_are_canonical_and_email_is_immutable(self):
        model = get_user_model()
        account = model.objects.create_user("fixed@example.com", self.password,
                                            role=" customer ", status=" Active ")
        self.assertEqual((account.role, account.status), ("CUSTOMER", "ACTIVE"))
        account.role = "Admin"
        account.status = "Locked"
        account.save(update_fields=["role", "status"])
        account.refresh_from_db()
        self.assertEqual((account.role, account.status), ("ADMIN", "LOCKED"))
        account.email = "changed@example.com"
        with self.assertRaises(ValidationError):
            account.save(update_fields=["email"])
        with self.assertRaises(ValidationError):
            model.objects.filter(pk=account.pk).update(email="changed@example.com")
        with self.assertRaises(ValidationError):
            model.objects.bulk_update([account], ["email"])
        account.refresh_from_db()
        self.assertEqual(account.email, "fixed@example.com")

    def test_locked_account_cannot_authenticate(self):
        account = get_user_model().objects.create_user("locked-login@example.com", self.password)
        self.assertEqual(authenticate(email=account.email, password=self.password), account)
        account.status = AccountStatus.LOCKED
        account.save(update_fields=["status"])
        self.assertIsNone(authenticate(email=account.email, password=self.password))

    def test_login_updates_last_login_and_lock_invalidates_existing_session(self):
        account = get_user_model().objects.create_user("session@example.com", self.password)
        self.assertIsNone(account.last_login)
        self.assertTrue(self.client.login(email=account.email, password=self.password))
        account.refresh_from_db()
        self.assertIsNotNone(account.last_login)
        request = RequestFactory().get("/")
        request.session = self.client.session
        self.assertEqual(get_user(request), account)

        account.status = AccountStatus.LOCKED
        account.save(update_fields=["status"])
        request.session = self.client.session
        self.assertTrue(get_user(request).is_anonymous)

    def test_manager_requires_email_and_password(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", self.password)
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("empty-password@example.com", "")
        with self.assertRaises(ValidationError):
            get_user_model().objects.create_user("weak@example.com", "123")

    def test_direct_raw_password_assignment_cannot_be_saved(self):
        account = get_user_model()(email="direct@example.com", password="raw-password", role=AccountRole.CUSTOMER)
        with self.assertRaises(ValidationError):
            account.save()
        self.assertFalse(get_user_model().objects.filter(email="direct@example.com").exists())

    def test_admin_creation_rejects_customer_role_or_locked_status(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser("role-admin@example.com", self.password, role=AccountRole.CUSTOMER)
        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser("locked-admin@example.com", self.password, status=AccountStatus.LOCKED)

    def test_physical_account_columns_match_official_schema(self):
        account_model = get_user_model()
        self.assertEqual(account_model._meta.db_table, "accounts")
        self.assertEqual(account_model._meta.pk.column, "account_id")
        self.assertEqual(account_model._meta.get_field("password").column, "password_hash")
        self.assertEqual(account_model._meta.get_field("last_login").column, "last_login_at")
        with connection.cursor() as cursor:
            columns = [column.name for column in connection.introspection.get_table_description(cursor, "accounts")]
        self.assertEqual(columns, [
            "account_id", "email", "password_hash", "role", "status",
            "last_login_at", "created_at", "updated_at",
        ])
