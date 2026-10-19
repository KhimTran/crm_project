from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import Account
from apps.catalog.models import Brand, Category, Product
from apps.customers.services import create_customer
from apps.feedback.constants import FeedbackStatus
from apps.feedback.errors import ProductNotAvailable
from apps.feedback.models import Feedback
from apps.feedback.services import create_feedback, handle_feedback

PASSWORD = "CrmFixture!2026"


# tv4: test 4.2.4 khách hàng gửi và xem phản hồi của mình
class CustomerFeedbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@example.com", "Quanly@12345")
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        category = Category.objects.create(category_name="Vợt")
        brand = Brand.objects.create(brand_name="Yonex")
        cls.racket = Product.objects.create(category=category, brand=brand,
                                            product_name="Astrox 88D", price=3500000)
        cls.old_racket = Product.objects.create(category=category, brand=brand,
                                                product_name="Vợt ngừng bán", price=1000000, status="INACTIVE")

    def setUp(self):
        self.an_password = PASSWORD
        self.an = create_customer(password=PASSWORD, email="an@example.com", full_name="An", phone="0900000001")
        self.binh = create_customer(password=PASSWORD, email="binh@example.com", full_name="Bình", phone="0900000002")
        self.client.login(email="an@example.com", password=self.an_password)

    def test_form_preselects_product_from_query_string(self):
        response = self.client.get(reverse("feedbacks:create"), {"product": self.racket.pk})
        self.assertContains(response, f'<option value="{self.racket.pk}" selected>')
        self.assertNotContains(response, "Vợt ngừng bán")

    def test_customer_submits_feedback_as_new(self):
        response = self.client.post(reverse("feedbacks:create"),
                                    {"product": self.racket.pk, "rating": 4, "content": "  Vợt đầm tay  "}, follow=True)
        self.assertRedirects(response, reverse("feedbacks:mine"))
        self.assertContains(response, "Cảm ơn bạn đã gửi phản hồi")
        feedback = Feedback.objects.get()
        self.assertEqual((feedback.customer, feedback.rating, feedback.content, feedback.status),
                         (self.an, 4, "Vợt đầm tay", FeedbackStatus.NEW))
        self.assertIsNone(feedback.handled_by)

    def test_feedback_menu_preserves_storefront_navigation_and_search(self):
        for path in ("/", "/products/", reverse("feedbacks:mine"), reverse("feedbacks:create")):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertContains(response, 'href="/feedbacks/mine/"')
                self.assertContains(response, "Phản hồi của tôi")
                self.assertContains(response, 'class="header-search"')
                self.assertContains(response, 'name="q"')
                self.assertContains(response, 'class="category-menu"')
                self.assertContains(response, 'class="account-menu"')
                if path.startswith("/feedbacks/"):
                    self.assertContains(response, 'href="/feedbacks/mine/" aria-current="page"')
        self.client.logout()
        self.assertNotContains(self.client.get("/"), 'href="/feedbacks/mine/"')

    def test_customer_submission_crm_reply_and_customer_view_through_http(self):
        response = self.client.post(reverse("feedbacks:create"), {
            "product": self.racket.pk, "rating": 4, "content": "Tôi cần hướng dẫn bảo quản vợt.",
        }, follow=True)
        self.assertRedirects(response, reverse("feedbacks:mine"))
        feedback = Feedback.objects.get(customer=self.an)
        self.assertEqual(feedback.status, FeedbackStatus.NEW)

        manager_client = Client()
        self.assertTrue(manager_client.login(email=self.manager.email, password="Quanly@12345"))
        reply = "Cất vợt ở nơi khô thoáng sau khi chơi."
        detail_url = reverse("crm_feedbacks:detail", args=[feedback.pk])
        response = manager_client.post(detail_url, {
            "status": FeedbackStatus.RESOLVED, "manager_note": reply,
        }, follow=True)
        self.assertRedirects(response, reverse("crm_feedbacks:list"))
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, FeedbackStatus.RESOLVED)
        self.assertEqual(feedback.handled_by, self.manager)
        self.assertIsNotNone(feedback.resolved_at)
        response = self.client.get(reverse("feedbacks:mine"))
        self.assertContains(response, reply)
        self.assertContains(response, "Đã xử lý")
        # Use an authenticated second customer to verify reply ownership.
        self.client.force_login(self.binh.account)
        self.assertNotContains(self.client.get(reverse("feedbacks:mine")), reply)

    def test_invalid_submission_is_rejected(self):
        for data in ({"product": self.racket.pk, "rating": 6, "content": "x"},
                     {"product": self.racket.pk, "rating": 5, "content": "   "},
                     {"product": self.old_racket.pk, "rating": 5, "content": "x"},
                     {"rating": 5, "content": "x"}):
            response = self.client.post(reverse("feedbacks:create"), data)
            self.assertEqual(response.status_code, 200)
        self.assertFalse(Feedback.objects.exists())
        with self.assertRaises(ProductNotAvailable):
            create_feedback(customer=self.an, product=self.old_racket, rating=5, content="x")

    def test_customer_sees_only_own_feedbacks_and_reply(self):
        mine = Feedback.objects.create(customer=self.an, product=self.racket, rating=3, content="Của An", status="NEW")
        Feedback.objects.create(customer=self.binh, product=self.racket, rating=1, content="Của Bình", status="NEW")
        handle_feedback(mine.pk, status=FeedbackStatus.RESOLVED, manager_note="Shop đã đổi vợt mới cho bạn",
                        handled_by=self.manager)
        response = self.client.get(reverse("feedbacks:mine"))
        self.assertContains(response, "Của An")
        self.assertContains(response, "Shop đã đổi vợt mới cho bạn")
        self.assertContains(response, "Đã xử lý")
        self.assertNotContains(response, "Của Bình")

    def test_staff_or_anonymous_cannot_use_customer_pages(self):
        self.client.logout()
        for url in (reverse("feedbacks:create"), reverse("feedbacks:mine")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("login", response.url)
        self.client.force_login(self.manager)
        self.client.post(reverse("feedbacks:create"), {"product": self.racket.pk, "rating": 5, "content": "x"})
        self.assertFalse(Feedback.objects.exists())

    def test_customer_without_profile_is_redirected(self):
        Account.objects.create_user("noprofile@example.com", "Khach@12345")
        self.client.login(email="noprofile@example.com", password="Khach@12345")
        response = self.client.get(reverse("feedbacks:create"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)


# tv4: test badge số phản hồi NEW trên menu CRM
class FeedbackBadgeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@example.com", "Quanly@12345")
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        category = Category.objects.create(category_name="Vợt")
        brand = Brand.objects.create(brand_name="Yonex")
        supplier = Supplier.objects.create(supplier_code="NCC01", supplier_name="NCC 1")
        product = Product.objects.create(category=category, brand=brand, supplier=supplier,
                                         product_name="Astrox 88D", price=3500000)
        customer = create_customer(password=PASSWORD, email="an@example.com", full_name="An", phone="0900000001")
        for status in ("NEW", "NEW", "RESOLVED"):
            Feedback.objects.create(customer=customer, product=product, rating=5, content="x", status=status)

    def test_menu_shows_new_feedback_count(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("customers:list"))
        self.assertEqual(response.context["new_feedback_count"], 2)
        self.assertContains(response, 'aria-label="2 phản hồi mới"')
