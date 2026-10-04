from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.errors import (
    AccountAlreadyActive, AccountAlreadyLocked, AccountDeleteProtectedError,
    AccountNotFound, AccountPermissionDenied, CannotDeleteOwnAccount,
    CannotLockOwnAccount, InvalidAccountRole, LastActiveAdminError,
    PasswordValidationError,
)
from apps.accounts.permissions import require_active_admin
from apps.accounts.selectors import get_account, list_accounts
from apps.accounts.selectors import list_account_page
from apps.accounts.services import (
    _protect_final_admin, change_account_role, create_account, delete_account, lock_account,
    reset_account_password, unlock_account,
)
from apps.accounts import services as account_services


class AccountServiceTests(TestCase):
    password = "StrongPass!2026"

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin@example.com", self.password)
        self.customer = get_user_model().objects.create_user("customer@example.com", self.password)

    def test_permission_guard_uses_current_database_status_and_role(self):
        self.assertEqual(require_active_admin(self.admin).pk, self.admin.pk)
        for actor in (AnonymousUser(), self.customer):
            with self.assertRaises(AccountPermissionDenied):
                list_accounts(actor)
            with self.assertRaises(AccountPermissionDenied):
                lock_account(actor, self.customer.pk)
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        with self.assertRaises(AccountPermissionDenied):
            get_account(self.admin, self.customer.pk)
        with self.assertRaises(AccountPermissionDenied):
            reset_account_password(self.admin, self.customer.pk, "AnotherStrong!2026")

    def test_read_selectors_exclude_password_hash(self):
        detail = get_account(self.admin, self.customer.pk)
        self.assertEqual(detail["account_id"], self.customer.pk)
        self.assertIn("last_login_at", detail)
        self.assertNotIn("password", detail)
        self.assertNotIn("password_hash", detail)
        self.assertEqual(len(list_accounts(self.admin)), 2)
        with self.assertRaises(AccountNotFound):
            get_account(self.admin, 999999)

    def test_self_protection_and_final_admin_lock(self):
        with self.assertRaises(CannotLockOwnAccount):
            lock_account(self.admin, self.admin.pk)
        with self.assertRaises(CannotDeleteOwnAccount):
            delete_account(self.admin, self.admin.pk)
        with self.assertRaises(LastActiveAdminError):
            _protect_final_admin(self.admin, [self.admin.pk])

    def test_lock_unlock_and_duplicate_actions(self):
        other = get_user_model().objects.create_superuser("other@example.com", self.password)
        result = lock_account(self.admin, other.pk)
        self.assertEqual(result["status"], AccountStatus.LOCKED)
        other.refresh_from_db()
        self.assertEqual(other.status, AccountStatus.LOCKED)
        self.assertIsNone(authenticate(email=other.email, password=self.password))
        with self.assertRaises(AccountAlreadyLocked):
            lock_account(self.admin, other.pk)
        self.assertEqual(unlock_account(self.admin, other.pk)["status"], AccountStatus.ACTIVE)
        with self.assertRaises(AccountAlreadyActive):
            unlock_account(self.admin, other.pk)

    def test_role_change_and_invalid_role(self):
        other = get_user_model().objects.create_superuser("other@example.com", self.password)
        self.assertEqual(change_account_role(self.admin, other.pk, AccountRole.CUSTOMER)["role"], AccountRole.CUSTOMER)
        with self.assertRaises(AccountPermissionDenied):
            change_account_role(other, self.admin.pk, AccountRole.CUSTOMER)
        with self.assertRaises(LastActiveAdminError):
            change_account_role(self.admin, self.admin.pk, AccountRole.CUSTOMER)
        with self.assertRaises(InvalidAccountRole):
            change_account_role(self.admin, self.customer.pk, "MANAGER")
        self.assertEqual(change_account_role(self.admin, self.customer.pk, AccountRole.CUSTOMER)["role"], AccountRole.CUSTOMER)
        with self.assertRaises(LastActiveAdminError):
            _protect_final_admin(self.admin, [self.admin.pk])

    def test_direct_services_and_selector_normalize_role_status(self):
        self.assertFalse(hasattr(account_services, "update_account_email"))
        created = create_account(self.admin, email=" CASE@EXAMPLE.COM ", role=" customer ",
                                 status=" Locked ", password=self.password)
        self.assertEqual((created["role"], created["status"]), ("CUSTOMER", "LOCKED"))
        self.assertEqual(created["email"], "case@example.com")
        self.assertEqual(change_account_role(self.admin, created["account_id"], "Admin")["role"], "ADMIN")
        page = list_account_page(self.admin, role=" admin ", status="locked")
        self.assertEqual(page.paginator.count, 1)
        with self.assertRaises(InvalidAccountRole):
            list_account_page(self.admin, role="STAFF")
        with self.assertRaises(ValueError):
            list_account_page(self.admin, status="ENABLED")

    def test_password_reset_validates_hashes_and_returns_only_id(self):
        new_password = "AnotherStrong!2026"
        result = reset_account_password(self.admin, self.customer.pk, new_password)
        self.assertEqual(result, {"account_id": self.customer.pk})
        self.customer.refresh_from_db()
        self.assertNotEqual(self.customer.password, new_password)
        self.assertTrue(self.customer.password.startswith("pbkdf2_"))
        self.assertIsNone(authenticate(email=self.customer.email, password=self.password))
        self.assertEqual(authenticate(email=self.customer.email, password=new_password), self.customer)
        with self.assertRaises(PasswordValidationError):
            reset_account_password(self.admin, self.customer.pk, "123")
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.check_password(new_password))

    def test_safe_delete_and_missing_target(self):
        result = delete_account(self.admin, self.customer.pk)
        self.assertEqual(result, {"account_id": self.customer.pk})
        self.assertFalse(get_user_model().objects.filter(pk=self.customer.pk).exists())
        with self.assertRaises(AccountNotFound):
            delete_account(self.admin, self.customer.pk)

    def test_admin_log_reference_is_preserved(self):
        log = LogEntry.objects.create(
            user=self.customer,
            content_type=ContentType.objects.get_for_model(get_user_model()),
            object_id=str(self.customer.pk),
            object_repr=self.customer.email,
            action_flag=1,
        )
        with self.assertRaises(AccountDeleteProtectedError):
            delete_account(self.admin, self.customer.pk)
        self.assertTrue(LogEntry.objects.filter(pk=log.pk, user=self.customer).exists())

    def test_final_admin_cannot_be_deleted(self):
        with self.assertRaises(CannotDeleteOwnAccount):
            delete_account(self.admin, self.admin.pk)
        self.assertTrue(get_user_model().objects.filter(pk=self.admin.pk).exists())


class AccountForeignKeyDeleteTests(TransactionTestCase):
    password = "StrongPass!2026"

    def test_restrict_reference_preserves_customer_record(self):
        admin = get_user_model().objects.create_superuser("admin@example.com", self.password)
        customer = get_user_model().objects.create_user("customer@example.com", self.password)
        from apps.customers.models import Customer
        Customer.objects.create(account=customer, full_name="Customer")
        with self.assertRaises(AccountDeleteProtectedError):
            delete_account(admin, customer.pk)
        self.assertTrue(get_user_model().objects.filter(pk=customer.pk).exists())
        with connection.cursor() as cursor:
            cursor.execute("SELECT account_id FROM customers WHERE account_id = %s", [customer.pk])
            self.assertEqual(cursor.fetchone()[0], customer.pk)

    def test_delete_view_preserves_referenced_customer_record(self):
        admin = get_user_model().objects.create_superuser("admin@example.com", self.password)
        customer = get_user_model().objects.create_user("customer@example.com", self.password)
        from apps.customers.models import Customer
        Customer.objects.create(account=customer, full_name="Customer")
        self.client.force_login(admin)
        response = self.client.post(reverse("accounts_admin:delete", args=[customer.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(pk=customer.pk).exists())
        with connection.cursor() as cursor:
            cursor.execute("SELECT account_id FROM customers WHERE account_id = %s", [customer.pk])
            self.assertEqual(cursor.fetchone()[0], customer.pk)

    def test_set_null_reference_preserves_handler_attribution(self):
        from apps.catalog.models import Brand, Category, Product, Supplier
        from apps.customers.models import Customer
        from apps.feedback.models import Feedback

        admin = get_user_model().objects.create_superuser("admin@example.com", self.password)
        handler = get_user_model().objects.create_user("handler@example.com", self.password)
        customer = Customer.objects.create(account=handler, full_name="Handler")
        product = Product.objects.create(
            category=Category.objects.create(category_name="Rackets"),
            brand=Brand.objects.create(brand_name="Demo brand"),
            supplier=Supplier.objects.create(supplier_code="TEST", supplier_name="Demo supplier"),
            product_name="Demo racket", price="100.00",
        )
        feedback = Feedback.objects.create(
            customer=customer, product=product, rating=5,
            content="Good", status="NEW", handled_by=handler,
        )
        with self.assertRaises(AccountDeleteProtectedError):
            delete_account(admin, handler.pk)
        feedback.refresh_from_db()
        self.assertEqual(feedback.handled_by_id, handler.pk)
