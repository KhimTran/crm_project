from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.accounts.constants import AccountStatus
from apps.accounts.models import Account
from apps.catalog.models import Brand, Category, Product, Supplier
from apps.customers.constants import CustomerStatus
from apps.customers.errors import CustomerAlreadyActive, CustomerAlreadyDeleted, CustomerAlreadyLocked
from apps.customers.models import Customer
from apps.customers.services import (
    create_customer, customer_related_counts, delete_customer, lock_customer, unlock_customer,
)
from apps.feedback.models import Feedback
from apps.surveys.models import Survey, SurveyRecipient, SurveyResponse


# tv4: tạo nhanh một khách hàng kèm mật khẩu để test đăng nhập
def make_customer(n=1):
    return create_customer(email=f"kh{n}@example.com", full_name=f"Khách {n}", phone=f"09000000{n:02d}")


class LockUnlockServiceTests(TestCase):
    def test_lock_blocks_login_and_unlock_restores_it(self):
        customer, password = make_customer()
        self.assertTrue(self.client.login(email=customer.account.email, password=password))
        self.client.logout()

        lock_customer(customer.pk)
        customer.account.refresh_from_db()
        self.assertEqual(customer.account.status, AccountStatus.LOCKED)
        self.assertFalse(self.client.login(email=customer.account.email, password=password))

        unlock_customer(customer.pk)
        customer.account.refresh_from_db()
        self.assertEqual(customer.account.status, AccountStatus.ACTIVE)
        self.assertTrue(self.client.login(email=customer.account.email, password=password))

    def test_lock_does_not_touch_other_customers_or_data(self):
        first, _ = make_customer(1)
        second, _ = make_customer(2)
        lock_customer(first.pk)
        second.account.refresh_from_db()
        self.assertEqual(second.account.status, AccountStatus.ACTIVE)
        self.assertEqual(Customer.objects.get(pk=first.pk).status, CustomerStatus.ACTIVE)

    def test_double_lock_and_double_unlock_are_rejected(self):
        customer, _ = make_customer()
        with self.assertRaises(CustomerAlreadyActive):
            unlock_customer(customer.pk)
        lock_customer(customer.pk)
        with self.assertRaises(CustomerAlreadyLocked):
            lock_customer(customer.pk)

    def test_deleted_customer_cannot_be_locked_or_unlocked(self):
        customer, _ = make_customer()
        delete_customer(customer.pk)
        for action in (lock_customer, unlock_customer, delete_customer):
            with self.assertRaises(CustomerAlreadyDeleted):
                action(customer.pk)


class DeleteServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@example.com", "Quanly@12345")
        category = Category.objects.create(category_name="Vợt")
        brand = Brand.objects.create(brand_name="Yonex")
        supplier = Supplier.objects.create(supplier_code="NCC01", supplier_name="NCC 1")
        cls.product = Product.objects.create(category=category, brand=brand, supplier=supplier,
                                             product_name="Astrox 88D", price=3500000)

    def test_soft_delete_keeps_history_and_locks_account(self):
        customer, password = make_customer()
        Feedback.objects.create(customer=customer, product=self.product, rating=5, content="Tốt", status="NEW")
        survey = Survey.objects.create(title="Vợt mới", status="OPEN", created_by=self.manager)
        recipient = SurveyRecipient.objects.create(survey=survey, customer=customer, status="COMPLETED")
        SurveyResponse.objects.create(recipient=recipient, status="SUBMITTED")
        self.assertEqual(customer_related_counts(customer),
                         {"feedbacks": 1, "surveys_sent": 1, "surveys_answered": 1})

        delete_customer(customer.pk)
        customer.refresh_from_db()
        customer.account.refresh_from_db()
        self.assertEqual(customer.status, CustomerStatus.DELETED)
        self.assertIsNotNone(customer.deleted_at)
        self.assertEqual(customer.account.status, AccountStatus.LOCKED)
        self.assertEqual(Feedback.objects.filter(customer=customer).count(), 1)
        self.assertEqual(SurveyRecipient.objects.filter(customer=customer).count(), 1)
        self.assertFalse(self.client.login(email=customer.account.email, password=password))


class LockDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@example.com", "Quanly@12345")
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        cls.staff = Account.objects.create_user("cskh@example.com", "Cskh@12345")
        cls.staff.groups.add(Group.objects.create(name="CUSTOMER_SERVICE"))

    def setUp(self):
        self.customer, self.password = make_customer()

    def status(self):
        return Account.objects.get(pk=self.customer.account.pk).status

    def test_manager_locks_with_reason_then_unlocks(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("customers:lock", args=[self.customer.pk]),
                                    {"reason": "Spam phản hồi"}, follow=True)
        self.assertEqual(self.status(), AccountStatus.LOCKED)
        self.assertContains(response, "Đã khóa tài khoản")
        self.assertContains(response, "Lý do: Spam phản hồi")
        self.assertContains(response, "Đã khóa")
        self.assertContains(response, "Mở khóa")

        response = self.client.post(reverse("customers:unlock", args=[self.customer.pk]), follow=True)
        self.assertEqual(self.status(), AccountStatus.ACTIVE)
        self.assertContains(response, "Đã mở khóa tài khoản")

    def test_lock_and_unlock_reject_get(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("customers:lock", args=[self.customer.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("customers:unlock", args=[self.customer.pk])).status_code, 405)
        self.assertEqual(self.status(), AccountStatus.ACTIVE)

    def test_locking_twice_shows_error_message(self):
        self.client.force_login(self.manager)
        self.client.post(reverse("customers:lock", args=[self.customer.pk]))
        response = self.client.post(reverse("customers:lock", args=[self.customer.pk]), follow=True)
        self.assertContains(response, "đã bị khóa")

    def test_unknown_customer_returns_404(self):
        self.client.force_login(self.manager)
        for name in ("lock", "unlock", "delete"):
            self.assertEqual(self.client.post(reverse(f"customers:{name}", args=[9999])).status_code, 404)

    def test_delete_confirm_page_then_post_soft_deletes(self):
        self.client.force_login(self.manager)
        url = reverse("customers:delete", args=[self.customer.pk])
        response = self.client.get(url)
        self.assertContains(response, "Bạn có chắc muốn xóa")
        self.assertContains(response, self.customer.customer_code)
        self.assertEqual(Customer.objects.get(pk=self.customer.pk).status, CustomerStatus.ACTIVE)

        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse("customers:list"))
        self.assertContains(response, "Đã xóa khách hàng")
        self.assertEqual(Customer.objects.get(pk=self.customer.pk).status, CustomerStatus.DELETED)
        self.assertEqual(self.status(), AccountStatus.LOCKED)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_customer_service_and_customer_cannot_lock_or_delete(self):
        other, other_password = make_customer(2)
        for login in (lambda: self.client.force_login(self.staff),
                      lambda: self.client.login(email=other.account.email, password=other_password)):
            login()
            self.client.post(reverse("customers:lock", args=[self.customer.pk]))
            self.client.post(reverse("customers:delete", args=[self.customer.pk]))
            self.assertEqual(self.status(), AccountStatus.ACTIVE)
            self.assertEqual(Customer.objects.get(pk=self.customer.pk).status, CustomerStatus.ACTIVE)
            self.client.logout()

    def test_locked_customer_session_is_cut_off(self):
        self.client.login(email=self.customer.account.email, password=self.password)
        lock_customer(self.customer.pk)
        response = self.client.get(reverse("customers:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
