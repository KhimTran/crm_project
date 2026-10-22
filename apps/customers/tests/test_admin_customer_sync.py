from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.errors import (
    CannotDemoteAdmin, CannotDemoteOwnAccount,
    CannotModifyOtherAdmin, CannotPromoteToAdmin,
)
from apps.accounts.selectors import list_account_page
from apps.accounts.services import (
    change_account_role, create_account, delete_account, lock_account, reset_account_password,
)
from apps.customers.models import Customer, CustomerPreference
from apps.customers.selectors import customer_queryset
from apps.customers.services import create_customer


class AdminCustomerSyncTests(TestCase):
    password = "StrongPassword!2026"

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("primary_admin@sync.test", self.password)
        self.second_admin = get_user_model().objects.create_superuser("second_admin@sync.test", self.password)
        self.manager = get_user_model().objects.create_user(
            "crm_manager@sync.test", self.password, role=AccountRole.MANAGER
        )

    def test_admin_creates_customer_account_auto_creates_profile(self):
        """ADMIN creating a CUSTOMER account automatically generates a linked Customer profile."""
        account_data = create_account(
            self.admin,
            email="admin_created_customer@sync.test",
            role=AccountRole.CUSTOMER,
            status=AccountStatus.ACTIVE,
            password=self.password,
        )
        # Check Account created
        account = get_user_model().objects.get(pk=account_data["account_id"])
        self.assertEqual(account.role, AccountRole.CUSTOMER)

        # Check linked Customer automatically created
        customer = Customer.objects.filter(pk=account.pk).first()
        self.assertIsNotNone(customer)
        self.assertEqual(customer.status, "ACTIVE")

    def test_cross_visibility_admin_and_manager(self):
        """CUSTOMER created by ADMIN appears in MANAGER list, and vice versa."""
        # 1. ADMIN creates a CUSTOMER account
        admin_created = create_account(
            self.admin,
            email="from_admin@sync.test",
            role=AccountRole.CUSTOMER,
            status=AccountStatus.ACTIVE,
            password=self.password,
        )
        # Verify it appears in MANAGER's customer_queryset
        qs_emails = list(customer_queryset().values_list("email", flat=True))
        self.assertIn("from_admin@sync.test", qs_emails)

        # 2. MANAGER creates a customer (via create_customer service)
        create_customer(
            email="from_manager@sync.test",
            password=self.password,
            full_name="Le Van Manager",
            phone="0911222333",
            play_styles=["Tấn công"],
            brands=["Yonex"],
        )
        # Verify it appears in ADMIN's list_account_page
        admin_page = list_account_page(self.admin, q="from_manager@sync.test")
        page_emails = [item["email"] for item in admin_page.object_list]
        self.assertIn("from_manager@sync.test", page_emails)

    def test_admin_can_delete_customer_created_by_manager(self):
        """ADMIN hard-deletes CUSTOMER accounts without business history created by MANAGER."""
        manager_customer = create_customer(
            email="manager_created_to_delete@sync.test",
            password=self.password,
            full_name="Customer By Manager",
            phone="0988777666",
            play_styles=["Phản tạt"],
            brands=["Victor"],
        )
        target_account_id = manager_customer.account_id

        # Verify Customer and Preferences exist
        self.assertTrue(Customer.objects.filter(pk=target_account_id).exists())
        self.assertTrue(CustomerPreference.objects.filter(customer_id=target_account_id).exists())

        # ADMIN deletes this customer account
        result = delete_account(self.admin, target_account_id)
        self.assertEqual(result, {"account_id": target_account_id})

        # Account, Customer and Preferences are hard deleted
        self.assertFalse(get_user_model().objects.filter(pk=target_account_id).exists())
        self.assertFalse(Customer.objects.filter(pk=target_account_id).exists())
        self.assertFalse(CustomerPreference.objects.filter(customer_id=target_account_id).exists())

    def test_admin_delete_customer_with_business_history_preserves_history(self):
        """Deleting a customer with feedback is blocked to protect business history."""
        from apps.accounts.errors import AccountDeleteProtectedError
        from apps.catalog.models import Brand, Category, Product
        from apps.feedback.models import Feedback

        customer = create_customer(
            email="customer_with_feedback@sync.test",
            password=self.password,
            full_name="History Customer",
            phone="0977666555",
        )
        product = Product.objects.create(
            category=Category.objects.create(category_name="Cat Test"),
            brand=Brand.objects.create(brand_name="Brand Test"),
            product_name="Product Test", price="20.00",
        )
        feedback = Feedback.objects.create(
            customer=customer, product=product, rating=4,
            content="Feedback content", status="NEW",
        )

        with self.assertRaises(AccountDeleteProtectedError):
            delete_account(self.admin, customer.account_id)

        # Account, Customer and feedback are preserved
        customer.refresh_from_db()
        self.assertEqual(customer.status, "ACTIVE")
        self.assertTrue(Feedback.objects.filter(pk=feedback.pk, customer=customer).exists())

    def test_admin_protection_rules(self):
        """Enforces all ADMIN protection constraints at backend layer."""
        # 1. No privilege escalation: cannot promote CUSTOMER or MANAGER to ADMIN
        customer_acc = get_user_model().objects.create_user("plain_customer@sync.test", self.password)
        with self.assertRaises(CannotPromoteToAdmin):
            change_account_role(self.admin, customer_acc.pk, AccountRole.ADMIN)

        with self.assertRaises(CannotPromoteToAdmin):
            change_account_role(self.admin, self.manager.pk, AccountRole.ADMIN)

        # 2. Cannot demote another ADMIN
        with self.assertRaises(CannotDemoteAdmin):
            change_account_role(self.admin, self.second_admin.pk, AccountRole.CUSTOMER)
        with self.assertRaises(CannotDemoteAdmin):
            change_account_role(self.admin, self.second_admin.pk, AccountRole.MANAGER)

        # 3. Cannot demote self
        with self.assertRaises(CannotDemoteOwnAccount):
            change_account_role(self.admin, self.admin.pk, AccountRole.CUSTOMER)
        with self.assertRaises(CannotDemoteOwnAccount):
            change_account_role(self.admin, self.admin.pk, AccountRole.MANAGER)

        # 4. Cannot lock another ADMIN
        with self.assertRaises(CannotModifyOtherAdmin):
            lock_account(self.admin, self.second_admin.pk)

        # 5. Cannot delete another ADMIN
        with self.assertRaises(CannotModifyOtherAdmin):
            delete_account(self.admin, self.second_admin.pk)

        # 6. Cannot reset password of another ADMIN
        with self.assertRaises(CannotModifyOtherAdmin):
            reset_account_password(self.admin, self.second_admin.pk, "NewPassword!2026")
