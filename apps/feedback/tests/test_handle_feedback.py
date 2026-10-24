from datetime import timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.catalog.models import Brand, Category, Product, Supplier
from apps.customers.services import create_customer
from apps.feedback.constants import FeedbackStatus
from apps.feedback.errors import FeedbackNoteRequired, FeedbackNotFound, InvalidFeedbackStatus
from apps.feedback.models import Feedback
from apps.feedback.selectors import feedback_queryset, filter_feedbacks
from apps.feedback.services import handle_feedback

PASSWORD = "CrmFixture!2026"


# tv4: dữ liệu dùng chung: 1 quản lý, 1 CSKH, 2 sản phẩm, 2 khách hàng
class FeedbackTestData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@example.com", "Quanly@12345")
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        cls.staff = Account.objects.create_user("cskh@example.com", "Cskh@12345")
        cls.staff.groups.add(Group.objects.create(name="CUSTOMER_SERVICE"))
        category = Category.objects.create(category_name="Vợt")
        brand = Brand.objects.create(brand_name="Yonex")
        supplier = Supplier.objects.create(supplier_code="NCC01", supplier_name="NCC 1")
        cls.racket = Product.objects.create(category=category, brand=brand, supplier=supplier,
                                            product_name="Astrox 88D", price=3500000)
        cls.shoe = Product.objects.create(category=category, brand=brand, supplier=supplier,
                                          product_name="Giày SHB 65Z3", price=2100000)
        cls.alice_password = PASSWORD
        cls.alice = create_customer(password=PASSWORD, email="an@example.com", full_name="Nguyễn Văn An",
                                                        phone="0900000001")
        cls.binh = create_customer(password=PASSWORD, email="binh@example.com", full_name="Trần Thị Bình", phone="0900000002")

    def make_feedback(self, customer=None, product=None, rating=5, content="Vợt rất tốt",
                      status=FeedbackStatus.NEW, days_ago=0):
        feedback = Feedback.objects.create(customer=customer or self.alice, product=product or self.racket,
                                           rating=rating, content=content, status=status)
        if days_ago:
            Feedback.objects.filter(pk=feedback.pk).update(created_at=timezone.now() - timedelta(days=days_ago))
            feedback.refresh_from_db()
        return feedback


# tv4: test 4.1.4 service xử lý: handled_by, resolved_at, trạng thái
class HandleFeedbackServiceTests(FeedbackTestData):
    def test_in_progress_sets_handler_without_resolved_at(self):
        feedback = self.make_feedback()
        handle_feedback(feedback.pk, status=FeedbackStatus.IN_PROGRESS, manager_note="", handled_by=self.staff)
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, FeedbackStatus.IN_PROGRESS)
        self.assertEqual(feedback.handled_by, self.staff)
        self.assertIsNone(feedback.resolved_at)
        self.assertIsNone(feedback.manager_note)

    def test_resolved_sets_reply_handler_and_resolved_at(self):
        feedback = self.make_feedback()
        handle_feedback(feedback.pk, status=FeedbackStatus.RESOLVED, manager_note="  Cảm ơn bạn!  ",
                        handled_by=self.manager)
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, FeedbackStatus.RESOLVED)
        self.assertEqual(feedback.manager_note, "Cảm ơn bạn!")
        self.assertEqual(feedback.handled_by, self.manager)
        self.assertIsNotNone(feedback.resolved_at)

    def test_editing_reply_keeps_first_resolved_at_and_reopen_clears_it(self):
        feedback = self.make_feedback()
        handle_feedback(feedback.pk, status=FeedbackStatus.RESOLVED, manager_note="Lần 1", handled_by=self.staff)
        first = Feedback.objects.get(pk=feedback.pk).resolved_at
        handle_feedback(feedback.pk, status=FeedbackStatus.RESOLVED, manager_note="Lần 2", handled_by=self.manager)
        feedback.refresh_from_db()
        self.assertEqual(feedback.resolved_at, first)
        self.assertEqual(feedback.manager_note, "Lần 2")
        self.assertEqual(feedback.handled_by, self.manager)

        handle_feedback(feedback.pk, status=FeedbackStatus.IN_PROGRESS, manager_note="Kiểm tra lại",
                        handled_by=self.staff)
        feedback.refresh_from_db()
        self.assertIsNone(feedback.resolved_at)
        self.assertEqual(feedback.status, FeedbackStatus.IN_PROGRESS)

    def test_invalid_input_is_rejected_without_changes(self):
        feedback = self.make_feedback()
        with self.assertRaises(FeedbackNoteRequired):
            handle_feedback(feedback.pk, status=FeedbackStatus.RESOLVED, manager_note="   ", handled_by=self.staff)
        for status in (FeedbackStatus.NEW, "DONE"):
            with self.assertRaises(InvalidFeedbackStatus):
                handle_feedback(feedback.pk, status=status, manager_note="x", handled_by=self.staff)
        with self.assertRaises(FeedbackNotFound):
            handle_feedback(9999, status=FeedbackStatus.IN_PROGRESS, manager_note="", handled_by=self.staff)
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, FeedbackStatus.NEW)
        self.assertIsNone(feedback.handled_by)


# tv4: test 4.1.4 bộ lọc phản hồi
class FilterFeedbackTests(FeedbackTestData):
    def setUp(self):
        self.recent = self.make_feedback(rating=5, content="Vợt nhẹ, dễ đánh")
        self.old = self.make_feedback(customer=self.binh, product=self.shoe, rating=2, content="Giày bị bong keo",
                                      status=FeedbackStatus.IN_PROGRESS, days_ago=10)

    def ids(self, **params):
        return set(filter_feedbacks(feedback_queryset(), params).values_list("pk", flat=True))

    def test_filters(self):
        self.assertEqual(self.ids(), {self.recent.pk, self.old.pk})
        self.assertEqual(self.ids(status=FeedbackStatus.NEW), {self.recent.pk})
        self.assertEqual(self.ids(product=self.shoe), {self.old.pk})
        self.assertEqual(self.ids(rating=2), {self.old.pk})
        self.assertEqual(self.ids(q="bình"), {self.old.pk})
        self.assertEqual(self.ids(q="bong keo"), {self.old.pk})

    def test_date_range_is_inclusive_by_day(self):
        today = timezone.localdate()
        old_day = timezone.localtime(self.old.created_at).date()
        self.assertEqual(self.ids(date_from=today), {self.recent.pk})
        self.assertEqual(self.ids(date_to=old_day), {self.old.pk})
        self.assertEqual(self.ids(date_from=old_day, date_to=today), {self.recent.pk, self.old.pk})


# tv4: test 4.1.4 trang danh sách / chi tiết phản hồi và phân quyền
class FeedbackViewTests(FeedbackTestData):
    def setUp(self):
        self.feedback = self.make_feedback(content="Cước căng bị lệch")

    def test_manager_and_staff_can_open_list_and_detail(self):
        for user in (self.manager, self.staff):
            self.client.force_login(user)
            response = self.client.get(reverse("crm_feedbacks:list"))
            self.assertContains(response, "Cước căng bị lệch")
            self.assertContains(response, "Mới")
            response = self.client.get(reverse("crm_feedbacks:detail", args=[self.feedback.pk]))
            self.assertContains(response, "Nguyễn Văn An")
            self.assertContains(response, "Astrox 88D")

    def test_list_filter_by_query_string(self):
        self.make_feedback(customer=self.binh, product=self.shoe, rating=1, content="Giày chật")
        self.client.force_login(self.staff)
        response = self.client.get(reverse("crm_feedbacks:list"), {"product": self.shoe.pk, "rating": 1})
        self.assertContains(response, "Giày chật")
        self.assertNotContains(response, "Cước căng bị lệch")

    def test_reversed_date_range_shows_error(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("crm_feedbacks:list"),
                                   {"date_from": "2026-10-05", "date_to": "2026-10-01"})
        self.assertContains(response, "Đến ngày phải sau hoặc bằng Từ ngày.")

    def test_staff_replies_and_resolves(self):
        self.client.force_login(self.staff)
        url = reverse("crm_feedbacks:detail", args=[self.feedback.pk])
        response = self.client.post(url, {"status": FeedbackStatus.RESOLVED,
                                          "manager_note": "Shop sẽ căng lại miễn phí."}, follow=True)
        self.assertRedirects(response, reverse("crm_feedbacks:list"))
        self.assertContains(response, "Đã cập nhật phản hồi")
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.status, FeedbackStatus.RESOLVED)
        self.assertEqual(self.feedback.handled_by, self.staff)
        self.assertEqual(self.feedback.manager_note, "Shop sẽ căng lại miễn phí.")
        self.assertIsNotNone(self.feedback.resolved_at)

    def test_resolve_without_reply_shows_error(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("crm_feedbacks:detail", args=[self.feedback.pk]),
                                    {"status": FeedbackStatus.RESOLVED, "manager_note": ""})
        self.assertContains(response, "Cần nhập câu trả lời")
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.status, FeedbackStatus.NEW)

    def test_unknown_feedback_returns_404(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("crm_feedbacks:detail", args=[9999])).status_code, 404)

    def test_customer_and_anonymous_cannot_handle(self):
        url = reverse("crm_feedbacks:detail", args=[self.feedback.pk])
        response = self.client.get(reverse("crm_feedbacks:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

        self.client.login(email=self.alice.account.email, password=self.alice_password)
        self.assertEqual(self.client.get(reverse("crm_feedbacks:list")).status_code, 302)
        self.client.post(url, {"status": FeedbackStatus.RESOLVED, "manager_note": "Tự trả lời"})
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.status, FeedbackStatus.NEW)
        self.assertIsNone(self.feedback.manager_note)
