from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.models import Account
from apps.customers.constants import CustomerStatus, PreferenceType
from apps.customers.errors import DuplicateCustomerEmail, DuplicateCustomerPhone
from apps.customers.models import Customer, CustomerPreference
from apps.customers.services import create_customer

PASSWORD = "CrmFixture!2026"

VALID = {
    "password": PASSWORD,
    "full_name": "Nguyễn Văn An",
    "email": "an.nguyen@example.com",
    "phone": "0901234567",
    "date_of_birth": "1995-05-20",
    "gender": "MALE",
    "address": "Quận 5, TP.HCM",
    "playing_level": "RECREATIONAL",
}


# tv4: test 4.1.1 service tạo khách hàng, trùng email / SĐT
class CreateCustomerServiceTests(TestCase):
    def test_creates_account_customer_and_preferences(self):
        password = PASSWORD
        customer = create_customer(password=PASSWORD,
            email="  An.Nguyen@Example.com ", full_name="Nguyễn Văn An", phone="0901234567",
            playing_level="BEGINNER", play_styles=["Tấn công"], brands=["Yonex", "Victor"])
        account = customer.account
        self.assertEqual(account.email, "an.nguyen@example.com")
        self.assertEqual(account.role, AccountRole.CUSTOMER)
        self.assertEqual(account.status, AccountStatus.ACTIVE)
        self.assertTrue(account.check_password(password))
        self.assertNotEqual(account.password, password)
        self.assertEqual(customer.status, CustomerStatus.ACTIVE)
        self.assertEqual(customer.customer_code, f"KH{customer.customer_id:04d}")
        prefs = set(CustomerPreference.objects.filter(customer=customer)
                    .values_list("preference_type", "preference_value"))
        self.assertEqual(prefs, {(PreferenceType.PLAY_STYLE, "Tấn công"),
                                 (PreferenceType.BRAND, "Yonex"), (PreferenceType.BRAND, "Victor")})

    def test_duplicate_email_is_rejected(self):
        create_customer(password=PASSWORD, email="a@example.com", full_name="A", phone="0901111111")
        with self.assertRaises(DuplicateCustomerEmail):
            create_customer(password=PASSWORD, email="A@example.com", full_name="B", phone="0902222222")

    def test_duplicate_phone_is_rejected_and_nothing_is_created(self):
        create_customer(password=PASSWORD, email="a@example.com", full_name="A", phone="0901111111")
        with self.assertRaises(DuplicateCustomerPhone):
            create_customer(password=PASSWORD, email="b@example.com", full_name="B", phone="0901111111")
        self.assertFalse(Account.objects.filter(email="b@example.com").exists())

    def test_deleted_customer_phone_can_be_reused(self):
        customer = create_customer(password=PASSWORD, email="a@example.com", full_name="A", phone="0901111111")
        from apps.customers.services import delete_customer
        delete_customer(customer.pk)
        new_customer = create_customer(password=PASSWORD, email="b@example.com", full_name="B", phone="0901111111")
        self.assertEqual(new_customer.phone, "0901111111")


# tv4: test 4.1.1 trang thêm khách hàng và phân quyền
class CustomerCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@example.com", "Quanly@12345")
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        cls.staff = Account.objects.create_user("cskh@example.com", "Cskh@12345")
        cls.staff.groups.add(Group.objects.create(name="CUSTOMER_SERVICE"))
        cls.shopper = Account.objects.create_user("shopper@example.com", "Khach@12345")
        cls.url = reverse("customers:create")

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_customer_and_customer_service_cannot_open_form(self):
        for account in (self.shopper, self.staff):
            self.client.force_login(account)
            response = self.client.post(self.url, VALID)
            self.assertNotEqual(response.status_code, 200)
            self.assertFalse(Customer.objects.filter(email=VALID["email"]).exists())

    def test_manager_sees_form(self):
        self.client.force_login(self.manager)
        response = self.client.get(self.url)
        self.assertContains(response, "Thêm khách hàng")
        self.assertContains(response, 'name="full_name"')

    def test_manager_creates_customer_without_disclosing_password(self):
        self.client.force_login(self.manager)
        response = self.client.post(self.url, VALID, follow=True)
        self.assertRedirects(response, reverse("customers:list"))
        customer = Customer.objects.get(phone="0901234567")
        self.assertEqual(customer.account.email, "an.nguyen@example.com")
        self.assertTrue(customer.account.check_password(PASSWORD))
        self.assertNotContains(response, PASSWORD)
        self.assertNotContains(response, "Mật khẩu tạm")
        self.assertContains(response, customer.customer_code)
        again = self.client.get(reverse("customers:list"))
        self.assertNotContains(again, "Mật khẩu tạm")

    def test_invalid_input_shows_errors_and_creates_nothing(self):
        self.client.force_login(self.manager)
        bad = {**VALID, "phone": "123", "email": "khong-hop-le", "date_of_birth": "2999-01-01"}
        response = self.client.post(self.url, bad)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid phone number")
        self.assertContains(response, "Invalid date of birth")
        self.assertFalse(Customer.objects.filter(email=bad["email"]).exists())

    def test_duplicate_email_and_phone_show_form_errors(self):
        self.client.force_login(self.manager)
        self.client.post(self.url, VALID)
        response = self.client.post(self.url, VALID)
        self.assertContains(response, "Email is already in use")
        self.assertContains(response, "Phone number is already in use")
        self.assertEqual(Customer.objects.filter(email=VALID["email"]).count(), 1)

    def test_list_searches_and_hides_deleted(self):
        self.client.force_login(self.manager)
        keep = create_customer(password=PASSWORD, email="keep@example.com", full_name="Trần Thị Bình", phone="0903333333")
        gone = create_customer(password=PASSWORD, email="gone@example.com", full_name="Lê Văn Cường", phone="0904444444")
        from apps.customers.services import delete_customer
        delete_customer(gone.pk)
        response = self.client.get(reverse("customers:list"), {"q": "Bình"})
        self.assertContains(response, "Trần Thị Bình")
        self.assertNotContains(response, "Lê Văn Cường")
        self.assertNotContains(self.client.get(reverse("customers:list")), "Lê Văn Cường")
