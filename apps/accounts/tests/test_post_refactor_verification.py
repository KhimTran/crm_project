import datetime
from django.apps import apps
from django.contrib.auth.models import Group
from django.db import connection
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.models import Account
from apps.catalog.models import Brand, Category, Product
from apps.customers.constants import CustomerStatus
from apps.customers.models import Customer, CustomerPreference
from apps.feedback.models import Feedback
from apps.surveys.models import Survey, SurveyRecipient


class PostRefactorSchemaTests(TestCase):
    """Xác minh mục 1 và 2: Loại bỏ hoàn toàn position, hire_date và suppliers."""

    def test_position_and_hire_date_not_in_model_or_db_schema(self):
        # 1. Model fields
        field_names = {f.name for f in Account._meta.get_fields()}
        self.assertNotIn("position", field_names)
        self.assertNotIn("hire_date", field_names)

        # 2. Database columns
        with connection.cursor() as cursor:
            columns = [col.name.lower() for col in connection.introspection.get_table_description(cursor, "accounts")]
        self.assertNotIn("position", columns)
        self.assertNotIn("hire_date", columns)

    def test_suppliers_table_and_model_completely_removed(self):
        # 1. Django model registry
        all_models = [m.__name__.lower() for m in apps.get_models()]
        self.assertNotIn("supplier", all_models)

        # 2. Database tables
        with connection.cursor() as cursor:
            tables = [t.lower() for t in connection.introspection.table_names(cursor)]
        self.assertNotIn("suppliers", tables)


class AdminCustomerEditTests(TestCase):
    """Xác minh mục 3: Quyền Admin chỉnh sửa hồ sơ khách hàng và bảo toàn quan hệ."""

    @classmethod
    def setUpTestData(cls):
        cls.password = "StrongPassword!2026"
        cls.admin = Account.objects.create_superuser("admin@postrefactor.test", cls.password)
        cls.manager = Account.objects.create_user("manager@postrefactor.test", cls.password, role=AccountRole.MANAGER)
        cls.crm_group = Group.objects.create(name="CRM_MANAGER")
        cls.manager.groups.add(cls.crm_group)

        # Customer account
        cls.customer_account = Account.objects.create_user(
            "customer@postrefactor.test",
            cls.password,
            role=AccountRole.CUSTOMER,
            status=AccountStatus.ACTIVE,
        )
        cls.customer = Customer.objects.get(pk=cls.customer_account.pk)
        cls.customer.full_name = "Original Customer Name"
        cls.customer.phone = "0901111222"
        cls.customer.address = "123 Initial Street"
        cls.customer.playing_level = "BEGINNER"
        cls.customer.date_of_birth = datetime.date(1995, 5, 20)
        cls.customer.gender = "MALE"
        cls.customer.save()

        # Another customer for duplicate test
        cls.other_account = Account.objects.create_user(
            "other@postrefactor.test",
            cls.password,
            role=AccountRole.CUSTOMER,
        )
        cls.other_customer = Customer.objects.get(pk=cls.other_account.pk)
        cls.other_customer.phone = "0909999888"
        cls.other_customer.save()

        # Related records: CustomerPreference, Feedback, SurveyRecipient
        cls.category = Category.objects.create(category_name="Rackets", status="ACTIVE")
        cls.brand = Brand.objects.create(brand_name="Yonex", status="ACTIVE")
        cls.product = Product.objects.create(
            product_name="Voltric Z-Force",
            category=cls.category,
            brand=cls.brand,
            price=150.00,
            status="ACTIVE",
        )
        cls.preference = CustomerPreference.objects.create(
            customer=cls.customer,
            preference_type="CATEGORY",
            preference_value="Rackets",
        )
        cls.feedback = Feedback.objects.create(
            customer=cls.customer,
            product=cls.product,
            rating=5,
            content="Great racket!",
            status="NEW",
        )
        cls.survey = Survey.objects.create(
            title="Post-Refactor Customer Survey",
            created_by=cls.admin,
            status="ACTIVE",
        )
        cls.survey_recipient = SurveyRecipient.objects.create(
            survey=cls.survey,
            customer=cls.customer,
            status="SENT",
        )

    def test_admin_can_edit_customer_profile_and_read_back(self):
        self.client.force_login(self.admin)
        original_hash = Account.objects.get(pk=self.customer_account.pk).password

        edit_url = reverse("customers:edit", args=[self.customer.pk])
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        # Post updated data
        updated_data = {
            "full_name": "Updated Customer Name",
            "email": "updated_customer@postrefactor.test",
            "phone": "0987654321",
            "address": "456 Renovated Ave, District 1",
            "playing_level": "COMPETITIVE",
            "date_of_birth": "1992-08-15",
            "gender": "FEMALE",
        }
        post_response = self.client.post(edit_url, updated_data, follow=True)
        self.assertRedirects(post_response, reverse("customers:detail", args=[self.customer.pk]))

        # Read back from database
        self.customer.refresh_from_db()
        self.customer_account.refresh_from_db()

        self.assertEqual(self.customer.full_name, "Updated Customer Name")
        self.assertEqual(self.customer_account.email, "updated_customer@postrefactor.test")
        self.assertEqual(self.customer.phone, "0987654321")
        self.assertEqual(self.customer.address, "456 Renovated Ave, District 1")
        self.assertEqual(self.customer.playing_level, "COMPETITIVE")
        self.assertEqual(self.customer.date_of_birth, datetime.date(1992, 8, 15))
        self.assertEqual(self.customer.gender, "FEMALE")

        # Invariants: role, status, password hash NOT changed
        self.assertEqual(self.customer_account.role, AccountRole.CUSTOMER)
        self.assertEqual(self.customer_account.status, AccountStatus.ACTIVE)
        self.assertEqual(self.customer_account.password, original_hash)

        # Related data preserved
        self.assertTrue(CustomerPreference.objects.filter(pk=self.preference.pk).exists())
        self.assertEqual(Feedback.objects.filter(customer=self.customer).count(), 1)
        self.assertEqual(SurveyRecipient.objects.filter(customer=self.customer).count(), 1)

    def test_admin_edit_validates_email_uniqueness(self):
        self.client.force_login(self.admin)
        edit_url = reverse("customers:edit", args=[self.customer.pk])

        # Attempt to use another account's email
        duplicate_data = {
            "full_name": "Duplicate Tester",
            "email": self.other_account.email,
            "phone": "0987654321",
            "address": "Anywhere",
        }
        response = self.client.post(edit_url, duplicate_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email is already in use.")

    def test_manager_can_edit_customer_within_crm_scope(self):
        self.client.force_login(self.manager)
        edit_url = reverse("customers:edit", args=[self.customer.pk])
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            "full_name": "Manager Edited Customer",
            "email": self.customer_account.email,
            "phone": "0912345678",
            "address": "Manager Street",
            "playing_level": "RECREATIONAL",
        }
        res = self.client.post(edit_url, post_data, follow=True)
        self.assertRedirects(res, reverse("customers:detail", args=[self.customer.pk]))

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.full_name, "Manager Edited Customer")
        self.assertEqual(self.customer.phone, "0912345678")

    def test_manager_blocked_from_admin_account_management(self):
        self.client.force_login(self.manager)
        # Manager is blocked from /admin/
        admin_account_url = reverse("accounts_admin:list")
        response = self.client.get(admin_account_url)
        # Manager cannot access /admin/ (redirected or forbidden)
        self.assertIn(response.status_code, (302, 403))

    def test_customer_cannot_edit_other_customer(self):
        self.client.force_login(self.other_account)
        edit_url = reverse("customers:edit", args=[self.customer.pk])
        response = self.client.get(edit_url)
        self.assertIn(response.status_code, (302, 403))
