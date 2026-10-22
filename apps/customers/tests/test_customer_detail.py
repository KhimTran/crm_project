from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.constants import AccountStatus
from apps.accounts.models import Account
from apps.catalog.models import Brand, Category, Product
from apps.customers.services import create_customer, delete_customer
from apps.feedback.models import Feedback

PASSWORD = "CrmFixture!2026"


# tv4: test trang chi tiết khách hàng và ẩn nút theo vai trò
class CustomerDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@example.com", "Quanly@12345")
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        cls.staff = Account.objects.create_user("cskh@example.com", "Cskh@12345")
        cls.staff.groups.add(Group.objects.create(name="CUSTOMER_SERVICE"))
        category = Category.objects.create(category_name="Vợt")
        brand = Brand.objects.create(brand_name="Yonex")
        cls.product = Product.objects.create(category=category, brand=brand,
                                             product_name="Astrox 88D", price=3500000)

    def setUp(self):
        self.password = PASSWORD
        self.customer = create_customer(password=PASSWORD,
            email="an@example.com", full_name="Nguyễn Văn An", phone="0900000001", date_of_birth=date(2000, 1, 2),
            gender="MALE", playing_level="COMPETITIVE", play_styles=["Tấn công"], brands=["Yonex", "Victor"])
        self.feedback = Feedback.objects.create(customer=self.customer, product=self.product, rating=4,
                                                content="Vợt đầm tay", status="RESOLVED", manager_note="Cảm ơn bạn")
        self.url = reverse("customers:detail", args=[self.customer.pk])

    def test_manager_sees_profile_preferences_and_feedback_history(self):
        self.client.force_login(self.manager)
        response = self.client.get(self.url)
        for text in ("KH", "Nguyễn Văn An", "02/01/2000", "Nam", "Thi đấu", "Tấn công", "Victor, Yonex",
                     "Astrox 88D", "Vợt đầm tay", "Cảm ơn bạn", "Đã xử lý"):
            self.assertContains(response, text)
        self.assertContains(response, reverse("crm_feedbacks:detail", args=[self.feedback.pk]))
        self.assertContains(response, reverse("customers:delete", args=[self.customer.pk]))

    def test_customer_service_can_view_but_manage_buttons_are_hidden(self):
        self.client.force_login(self.staff)
        for url in (self.url, reverse("customers:list")):
            response = self.client.get(url)
            self.assertContains(response, "Nguyễn Văn An")
            self.assertNotContains(response, reverse("customers:delete", args=[self.customer.pk]))
            self.assertNotContains(response, reverse("customers:lock", args=[self.customer.pk]))
            self.assertNotContains(response, reverse("customers:create"))

    def test_lock_from_detail_returns_to_detail(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("customers:lock", args=[self.customer.pk]), {"from": "detail"})
        self.assertRedirects(response, self.url)
        self.assertEqual(Account.objects.get(pk=self.customer.account.pk).status, AccountStatus.LOCKED)
        self.assertContains(self.client.get(self.url), "Mở khóa")

    def test_deleted_or_unknown_customer_returns_404(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("customers:detail", args=[9999])).status_code, 404)
        self.feedback.delete()
        delete_customer(self.customer.pk)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_customer_account_cannot_view(self):
        self.client.login(email="an@example.com", password=self.password)
        self.assertEqual(self.client.get(self.url).status_code, 302)
