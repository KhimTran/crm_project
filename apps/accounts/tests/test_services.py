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
    CannotLockOwnAccount, CannotDemoteAdmin, CannotDemoteOwnAccount,
    CannotModifyOtherAdmin, CannotPromoteToAdmin, InvalidAccountRole,
    LastActiveAdminError, PasswordValidationError,
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
        with self.assertRaises(CannotDemoteOwnAccount):
            change_account_role(self.admin, self.admin.pk, AccountRole.CUSTOMER)
        with self.assertRaises(CannotDemoteOwnAccount):
            change_account_role(self.admin, self.admin.pk, AccountRole.MANAGER)
        with self.assertRaises(LastActiveAdminError):
            _protect_final_admin(self.admin, [self.admin.pk])

    def test_lock_unlock_and_duplicate_actions(self):
        other = get_user_model().objects.create_superuser("other@example.com", self.password)
        with self.assertRaises(CannotModifyOtherAdmin):
            lock_account(self.admin, other.pk)

        target = get_user_model().objects.create_user("target_lock@example.com", self.password)
        result = lock_account(self.admin, target.pk)
        self.assertEqual(result["status"], AccountStatus.LOCKED)
        target.refresh_from_db()
        self.assertEqual(target.status, AccountStatus.LOCKED)
        self.assertIsNone(authenticate(email=target.email, password=self.password))
        with self.assertRaises(AccountAlreadyLocked):
            lock_account(self.admin, target.pk)
        self.assertEqual(unlock_account(self.admin, target.pk)["status"], AccountStatus.ACTIVE)
        with self.assertRaises(AccountAlreadyActive):
            unlock_account(self.admin, target.pk)

    def test_role_change_and_invalid_role(self):
        other = get_user_model().objects.create_superuser("other@example.com", self.password)
        # Cannot demote another admin
        with self.assertRaises(CannotDemoteAdmin):
            change_account_role(self.admin, other.pk, AccountRole.CUSTOMER)
        with self.assertRaises(CannotDemoteAdmin):
            change_account_role(self.admin, other.pk, AccountRole.MANAGER)
        with self.assertRaises(AccountPermissionDenied):
            change_account_role(self.customer, self.admin.pk, AccountRole.CUSTOMER)

        # Cannot demote self
        with self.assertRaises(CannotDemoteOwnAccount):
            change_account_role(self.admin, self.admin.pk, AccountRole.CUSTOMER)
        with self.assertRaises(CannotDemoteOwnAccount):
            change_account_role(self.admin, self.admin.pk, AccountRole.MANAGER)

        # Cannot promote customer or manager to admin
        with self.assertRaises(CannotPromoteToAdmin):
            change_account_role(self.admin, self.customer.pk, AccountRole.ADMIN)

        # Can change between non-admin roles
        self.assertEqual(change_account_role(self.admin, self.customer.pk, "MANAGER")["role"], AccountRole.MANAGER)
        with self.assertRaises(InvalidAccountRole):
            change_account_role(self.admin, self.customer.pk, "STAFF")
        self.assertEqual(change_account_role(self.admin, self.customer.pk, AccountRole.CUSTOMER)["role"], AccountRole.CUSTOMER)
        with self.assertRaises(LastActiveAdminError):
            _protect_final_admin(self.admin, [self.admin.pk])

    def test_direct_services_and_selector_normalize_role_status(self):
        self.assertFalse(hasattr(account_services, "update_account_email"))
        created = create_account(self.admin, email=" CASE@EXAMPLE.COM ", role=" customer ",
                                 status=" Locked ", password=self.password)
        self.assertEqual((created["role"], created["status"]), ("CUSTOMER", "LOCKED"))
        self.assertEqual(created["email"], "case@example.com")
        self.assertEqual(change_account_role(self.admin, created["account_id"], "Manager")["role"], "MANAGER")
        page = list_account_page(self.admin, role=" manager ", status="locked")
        self.assertEqual(page.paginator.count, 1)
        with self.assertRaises(InvalidAccountRole):
            list_account_page(self.admin, role="STAFF")
        with self.assertRaises(ValueError):
            list_account_page(self.admin, status="ENABLED")

    def test_password_reset_validates_hashes_and_returns_only_id(self):
        other_admin = get_user_model().objects.create_superuser("other_admin_pwd@example.com", self.password)
        with self.assertRaises(CannotModifyOtherAdmin):
            reset_account_password(self.admin, other_admin.pk, "AnotherStrong!2026")

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
        other_admin = get_user_model().objects.create_superuser("other_admin_del@example.com", self.password)
        with self.assertRaises(CannotModifyOtherAdmin):
            delete_account(self.admin, other_admin.pk)

        result = delete_account(self.admin, self.customer.pk)
        self.assertEqual(result, {"account_id": self.customer.pk})
        self.assertFalse(get_user_model().objects.filter(pk=self.customer.pk).exists())
        with self.assertRaises(AccountNotFound):
            delete_account(self.admin, self.customer.pk)

    def test_create_account_auto_creates_customer_profile(self):
        from apps.customers.models import Customer
        created = create_account(self.admin, email="autocus@example.com", role=AccountRole.CUSTOMER,
                                 status=AccountStatus.ACTIVE, password=self.password)
        customer = Customer.objects.filter(account_id=created["account_id"]).first()
        self.assertIsNotNone(customer)
        self.assertEqual(customer.full_name, "")
        self.assertEqual(customer.status, "ACTIVE")

        # Creating a MANAGER account does not create a Customer profile
        mgr_data = create_account(self.admin, email="automgr@example.com", role=AccountRole.MANAGER,
                                  status=AccountStatus.ACTIVE, password=self.password)
        self.assertFalse(Customer.objects.filter(account_id=mgr_data["account_id"]).exists())

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

    def test_customer_without_history_is_hard_deleted(self):
        admin = get_user_model().objects.create_superuser("admin@example.com", self.password)
        customer = get_user_model().objects.create_user("customer@example.com", self.password, full_name="Customer")
        result = delete_account(admin, customer.pk)
        self.assertEqual(result, {"account_id": customer.pk})
        self.assertFalse(get_user_model().objects.filter(pk=customer.pk).exists())

    def test_customer_with_history_raises_protected_error(self):
        from apps.catalog.models import Brand, Category, Product
        from apps.feedback.models import Feedback

        admin = get_user_model().objects.create_superuser("admin@example.com", self.password)
        customer = get_user_model().objects.create_user("customer@example.com", self.password, full_name="Customer")
        product = Product.objects.create(
            category=Category.objects.create(category_name="Rackets"),
            brand=Brand.objects.create(brand_name="Demo brand"),
            product_name="Demo racket", price="100.00",
        )
        feedback = Feedback.objects.create(
            customer=customer, product=product, rating=5,
            content="Good", status="NEW",
        )
        with self.assertRaises(AccountDeleteProtectedError):
            delete_account(admin, customer.pk)
        self.assertTrue(get_user_model().objects.filter(pk=customer.pk).exists())
        self.assertTrue(Feedback.objects.filter(pk=feedback.pk).exists())
