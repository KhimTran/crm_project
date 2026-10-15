from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.customers.services import create_customer


# tv4: Admin vào được trang khách hàng / phản hồi từ sidebar Admin Portal
class AdminAccessTests(TestCase):
    password = "StrongPass!2026"

    # tv4: tạo admin đăng nhập sẵn và một khách hàng mẫu
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin@example.test", self.password)
        self.customer, _ = create_customer(email="kh1@example.com", full_name="Khách 1", phone="0900000001")
        self.client.login(email=self.admin.email, password=self.password)

    # Admin Portal sidebar chỉ có Accounts và Database Tools, không chứa CRM modules
    def test_admin_portal_sidebar_links_customers_and_feedback(self):
        response = self.client.get(reverse("accounts_admin:list"))
        self.assertContains(response, f'href="{reverse("accounts_admin:list")}"')
        self.assertContains(response, f'href="{reverse("database_tools")}"')
        self.assertNotContains(response, f'href="{reverse("customers:list")}"')
        self.assertNotContains(response, f'href="{reverse("crm_feedbacks:list")}"')
        self.assertNotContains(response, "Planned")

    # tv4: admin mở được các trang xem của TV4
    def test_admin_can_open_customer_and_feedback_pages(self):
        for url in (reverse("customers:list"), reverse("customers:detail", args=[self.customer.pk]),
                    reverse("customers:create"), reverse("crm_feedbacks:list"),
                    reverse("customer_reports:customers")):
            self.assertEqual(self.client.get(url).status_code, 200, url)

    # tv4: admin thấy nút quản lý (thêm khách hàng) như Quản lý CRM
    def test_admin_sees_manage_actions(self):
        response = self.client.get(reverse("customers:list"))
        self.assertContains(response, reverse("customers:create"))

    # tv4: admin xem trang TV4 trong khung Admin Portal, Quản lý CRM vẫn dùng khung CRM
    def test_layout_follows_role(self):
        response = self.client.get(reverse("crm_feedbacks:list"))
        self.assertTemplateUsed(response, "admin_portal/base.html")
        self.assertContains(response, "crm_portal.css")

        manager = get_user_model().objects.create_user("manager@example.test", self.password)
        manager.groups.add(Group.objects.get_or_create(name="CRM_MANAGER")[0])
        self.client.force_login(manager)
        response = self.client.get(reverse("customers:list"))
        self.assertTemplateUsed(response, "layouts/base_crm.html")
        self.assertTemplateNotUsed(response, "admin_portal/base.html")

    # tv4: trong Admin Portal nội dung tiếng Anh (nhãn, lựa chọn, lỗi form, thông báo); Quản lý CRM vẫn tiếng Việt
    def test_admin_portal_content_is_english(self):
        response = self.client.get(reverse("customers:list"))
        self.assertContains(response, "Create Customer")
        self.assertContains(response, "Playing Level")
        self.assertContains(response, "Beginner")
        self.assertNotContains(response, "Thêm khách hàng")

        for url, text in ((reverse("crm_feedbacks:list"), "Customer Feedback"),
                          (reverse("customers:detail", args=[self.customer.pk]), "Customer Information"),
                          (reverse("customer_reports:customers"), "Customers by Age Group")):
            self.assertContains(self.client.get(url), text)

        response = self.client.post(reverse("customers:create"), {"full_name": "A", "email": "x@example.com",
                                                                   "phone": "123"})
        self.assertContains(response, "Invalid phone number")

        response = self.client.post(reverse("customers:lock", args=[self.customer.pk]), {"reason": "spam"}, follow=True)
        self.assertContains(response, "locked. Reason: spam")

        manager = get_user_model().objects.create_user("manager@example.test", self.password)
        manager.groups.add(Group.objects.get_or_create(name="CRM_MANAGER")[0])
        self.client.force_login(manager)
        response = self.client.get(reverse("customers:list"))
        self.assertContains(response, "Thêm khách hàng")
        self.assertNotContains(response, "Create Customer")
