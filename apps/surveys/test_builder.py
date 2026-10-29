"""tv4: trang Tạo/Sửa khảo sát (trình soạn): validation, thứ tự câu hỏi, lưu Nháp, phát hành, khóa sửa."""
import json
from datetime import timedelta

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.constants import AccountStatus
from apps.accounts.models import Account
from apps.customers.models import Customer
from .constants import MANAGER_GROUP, SurveyStatus
from .models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient, SurveyResponse

PW = "StrongPass!2026"


# tv4: tạo khách hàng (mặc định đang hoạt động)
def make_customer(email, name, phone, locked=False):
    account = Account.objects.create_user(email, PW)
    if locked:
        Account.objects.filter(pk=account.pk).update(status=AccountStatus.LOCKED)
    return Customer.objects.create(account=account, full_name=name, phone=phone, playing_level="BEGINNER")


# tv4: câu hỏi dạng JSON như trình soạn (JS) gửi lên
def question(text, kind="SINGLE_CHOICE", options=("Có", "Không"), **extra):
    return {"text": text, "type": kind, "required": True, "options": list(options), **extra}


class SurveyBuilderTests(TestCase):
    # tv4: quản lý CRM, 2 khách hợp lệ và 1 khách bị khóa
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("builder-manager@test.vn", PW)
        cls.manager.groups.add(Group.objects.get_or_create(name=MANAGER_GROUP)[0])
        cls.an = make_customer("an@test.vn", "Nguyễn An", "0901000001")
        cls.binh = make_customer("binh@test.vn", "Trần Bình", "0901000002")
        cls.locked = make_customer("khoa@test.vn", "Lê Khóa", "0901000003", locked=True)

    def setUp(self):
        self.client.force_login(self.manager)

    # tv4: dữ liệu form hợp lệ tối thiểu (ngày định dạng yyyy-mm-dd của ô chọn ngày)
    def payload(self, questions=(), action="save", **overrides):
        today = timezone.localdate()
        data = {"title": "Khảo sát mới", "objective": "SATISFACTION", "description": "Mô tả",
                "start_at": today.isoformat(), "end_at": (today + timedelta(days=7)).isoformat(),
                "audience": "all", "action": action, "questions_json": json.dumps(list(questions))}
        data.update(overrides)
        return data

    def create(self, questions=(), **overrides):
        return self.client.post(reverse("surveys:manage_create"), self.payload(questions, **overrides))

    # ───── validation ngày ─────
    def test_end_date_before_start_date_is_rejected(self):
        today = timezone.localdate()
        response = self.create(start_at=(today + timedelta(days=3)).isoformat(), end_at=(today + timedelta(days=2)).isoformat())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu.")
        self.assertFalse(Survey.objects.exists())

    def test_start_date_in_the_past_is_rejected_when_creating(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        response = self.create(start_at=yesterday.isoformat())
        self.assertContains(response, "Ngày bắt đầu không được ở quá khứ.")
        self.assertFalse(Survey.objects.exists())

    def test_same_start_and_end_day_is_allowed_and_covers_the_whole_day(self):
        today = timezone.localdate()
        self.create(start_at=today.isoformat(), end_at=today.isoformat())
        survey = Survey.objects.get()
        self.assertEqual(timezone.localtime(survey.start_at).time().isoformat(), "00:00:00")
        self.assertEqual(timezone.localtime(survey.end_at).time().isoformat(), "23:59:59")

    def test_dd_mm_yyyy_dates_are_accepted(self):
        today = timezone.localdate()
        self.create(start_at=today.strftime("%d/%m/%Y"), end_at=(today + timedelta(days=1)).strftime("%d/%m/%Y"))
        self.assertEqual(timezone.localtime(Survey.objects.get().start_at).date(), today)

    def test_required_fields(self):
        response = self.create(title="", objective="", audience="")
        self.assertEqual(response.status_code, 200)
        for name in ("title", "objective"):
            self.assertTrue(response.context["form"].errors.get(name), name)
        self.assertTrue(response.context["audience_form"].errors.get("audience"))
        self.assertFalse(Survey.objects.exists())

    # ───── phương án trả lời ─────
    def test_choice_question_needs_two_options(self):
        response = self.create([question("Q1", options=["Chỉ một"])])
        self.assertEqual(response.status_code, 200)
        self.assertIn("options", response.context["builder"]["errors"]["0"])
        self.assertFalse(Survey.objects.exists())

    def test_duplicate_or_empty_options_are_rejected(self):
        response = self.create([question("Q1", options=["Có", "có"]), question("Q2", options=["A", ""])])
        errors = response.context["builder"]["errors"]
        self.assertIn("Các phương án trả lời không được trùng nhau.", errors["0"]["options"])
        self.assertIn("Phương án trả lời không được để trống.", errors["1"]["options"])
        self.assertFalse(Survey.objects.exists())

    def test_max_selections_must_not_exceed_option_count(self):
        response = self.create([question("Q", "MULTI_CHOICE", ["A", "B"], max_selections=3)])
        self.assertIn("max_selections", response.context["builder"]["errors"]["0"])

    def test_rating_needs_min_below_max(self):
        response = self.create([question("Q", "RATING", [], rating_min=5, rating_max=5)])
        self.assertIn("rating", response.context["builder"]["errors"]["0"])

    def test_errors_keep_every_question_the_user_typed(self):
        typed = [question("Câu hợp lệ"), question("", "TEXT", [])]
        response = self.create(typed)
        self.assertEqual([q["text"] for q in response.context["builder_items"]], ["Câu hợp lệ", ""])
        self.assertEqual(list(response.context["builder"]["errors"]), ["1"])

    # ───── lưu câu hỏi ─────
    def test_draft_can_be_saved_without_questions(self):
        response = self.create([])
        survey = Survey.objects.get()
        self.assertRedirects(response, reverse("surveys:manage_edit", args=[survey.pk]))
        self.assertEqual((survey.status, survey.objective, survey.surveyquestion_set.count()),
                         (SurveyStatus.DRAFT, "SATISFACTION", 0))
        self.assertEqual(survey.audience["audience"], "all")

    def test_question_order_and_settings_are_saved(self):
        self.create([
            question("Q1"),
            question("Q2", "MULTI_CHOICE", ["A", "B", "C"], max_selections=2, other=True, other_label="Khác"),
            question("Q3", "RATING", [], rating_min=1, rating_max=10, rating_min_label="Tệ", rating_max_label="Tốt"),
            question("Q4", "TEXT", [], placeholder="Góp ý", required=False),
        ])
        survey = Survey.objects.get()
        rows = list(survey.surveyquestion_set.order_by("sort_order"))
        self.assertEqual([(q.question_text, q.sort_order) for q in rows], [("Q1", 1), ("Q2", 2), ("Q3", 3), ("Q4", 4)])
        multi, rating, text = rows[1], rows[2], rows[3]
        options = list(multi.surveyoption_set.order_by("sort_order").values_list("option_text", flat=True))
        self.assertEqual(options, ["A", "B", "C", "Khác"])
        self.assertEqual(multi.config["max_selections"], 2)
        self.assertEqual(SurveyOption.objects.get(pk=multi.config["other_option_id"]).option_text, "Khác")
        self.assertEqual((rating.config["rating_max"], rating.config["rating_min_label"], rating.config["rating_max_label"]),
                         (10, "Tệ", "Tốt"))
        self.assertEqual((text.config["placeholder"], text.is_required), ("Góp ý", False))

    def test_edit_page_loads_saved_data_and_reorder_is_saved(self):
        self.create([question("Q1"), question("Q2", "MULTI_CHOICE", ["A", "B"], other=True, other_label="Khác"),
                     question("Q3", "TEXT", [])])
        survey = Survey.objects.get()
        page = self.client.get(reverse("surveys:manage_edit", args=[survey.pk]))
        self.assertEqual(page.context["mode"], "edit")
        self.assertContains(page, "Chỉnh sửa khảo sát")
        items = page.context["builder_items"]
        self.assertEqual([i["text"] for i in items], ["Q1", "Q2", "Q3"])
        self.assertEqual((items[1]["options"], items[1]["other"], items[1]["other_label"]), (["A", "B"], True, "Khác"))
        self.assertEqual(page.context["form"]["objective"].value(), "SATISFACTION")
        # kéo thả: Q3 lên đầu, bỏ Q2
        reordered = [items[2], items[0]]
        self.client.post(reverse("surveys:manage_edit", args=[survey.pk]), self.payload(reordered))
        self.assertEqual(list(survey.surveyquestion_set.order_by("sort_order").values_list("question_text", "sort_order")),
                         [("Q3", 1), ("Q1", 2)])

    def test_save_add_returns_to_editor_with_new_question_flag(self):
        response = self.create([question("Q1")], action="save_add")
        survey = Survey.objects.get()
        self.assertRedirects(response, reverse("surveys:manage_edit", args=[survey.pk]) + "?add=1",
                             fetch_redirect_response=False)
        self.assertTrue(self.client.get(response.url).context["builder"]["addOnLoad"])

    def test_audience_is_saved_with_the_draft(self):
        self.create([], audience="pick", customer_ids=[self.an.pk])
        survey = Survey.objects.get()
        self.assertEqual(survey.audience["customer_ids"], [self.an.pk])
        page = self.client.get(reverse("surveys:manage_edit", args=[survey.pk]))
        self.assertEqual(page.context["audience_form"]["audience"].value(), "pick")
        self.assertEqual([c["id"] for c in page.context["customers"] if c["checked"]], [self.an.pk])

    def test_locked_customers_are_not_listed_or_accepted(self):
        page = self.client.get(reverse("surveys:manage_create"))
        self.assertNotIn(self.locked.pk, [c["id"] for c in page.context["customers"]])
        self.create([], audience="pick", customer_ids=[self.locked.pk])
        self.assertFalse(Survey.objects.exists())

    def test_repeated_submit_with_same_form_token_creates_one_survey(self):
        data = self.payload([question("Q1")], form_token="a" * 32)
        first = self.client.post(reverse("surveys:manage_create"), data)
        second = self.client.post(reverse("surveys:manage_create"), data)
        survey = Survey.objects.get()
        self.assertEqual(first.url, second.url)
        self.assertEqual(second.url, reverse("surveys:manage_edit", args=[survey.pk]))

    # ───── phát hành ─────
    def test_publish_sends_to_audience_and_opens_survey(self):
        response = self.create([question("Q1")], action="publish")
        survey = Survey.objects.get()
        self.assertRedirects(response, reverse("surveys:manage_detail", args=[survey.pk]), fetch_redirect_response=False)
        self.assertEqual(survey.status, SurveyStatus.ACTIVE)
        self.assertEqual(set(SurveyRecipient.objects.filter(survey=survey).values_list("customer_id", flat=True)),
                         {self.an.pk, self.binh.pk})

    def test_publish_blocked_without_questions(self):
        response = self.create([], action="publish")
        self.assertContains(response, "The survey has no questions yet.")
        self.assertFalse(Survey.objects.exists())

    def test_publish_blocked_without_recipients_keeps_typed_data(self):
        response = self.create([question("Q1")], action="publish", audience="filter", age_groups=["55p"])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chưa có khách hàng nào phù hợp để nhận khảo sát.")
        self.assertFalse(Survey.objects.exists())  # rollback toàn bộ
        self.assertEqual(response.context["builder_items"][0]["text"], "Q1")

    def test_publish_existing_draft_from_edit_page(self):
        self.create([question("Q1")])
        survey = Survey.objects.get()
        self.client.post(reverse("surveys:manage_edit", args=[survey.pk]),
                         self.payload([question("Q1")], action="publish", audience="pick", customer_ids=[self.binh.pk]))
        survey.refresh_from_db()
        self.assertEqual(survey.status, SurveyStatus.ACTIVE)
        self.assertEqual(list(SurveyRecipient.objects.filter(survey=survey).values_list("customer_id", flat=True)),
                         [self.binh.pk])

    def test_audience_count_endpoint(self):
        url = reverse("surveys:manage_audience_count")
        self.assertEqual(self.client.get(url, {"audience": "all"}).json(), {"count": 2})
        self.assertEqual(self.client.get(url, {"audience": "pick", "customer_ids": [self.an.pk]}).json(), {"count": 1})
        self.assertEqual(self.client.get(url, {"audience": "pick"}).status_code, 400)

    # ───── khóa sửa ─────
    def test_questions_cannot_be_edited_after_answers(self):
        self.create([question("Q1")], action="publish")
        survey = Survey.objects.get()
        q1 = survey.surveyquestion_set.get()
        recipient = SurveyRecipient.objects.filter(survey=survey).first()
        response_row = SurveyResponse.objects.create(recipient=recipient, status="SUBMITTED", submitted_at=timezone.now())
        SurveyAnswer.objects.create(response=response_row, question=q1, option=q1.surveyoption_set.first())
        page = self.client.get(reverse("surveys:manage_edit", args=[survey.pk]))
        self.assertEqual(page.context["mode"], "readonly")
        self.assertTrue(page.context["form"].fields["title"].disabled)
        response = self.client.post(reverse("surveys:manage_edit", args=[survey.pk]),
                                    self.payload([question("Đã đổi")], title="Đổi tên"))
        self.assertRedirects(response, reverse("surveys:manage_edit", args=[survey.pk]), fetch_redirect_response=False)
        survey.refresh_from_db()
        self.assertEqual(survey.title, "Khảo sát mới")
        self.assertEqual(list(survey.surveyquestion_set.values_list("question_text", flat=True)), ["Q1"])
        self.assertTrue(SurveyAnswer.objects.filter(question=q1).exists())

    def test_closed_survey_is_view_only(self):
        self.create([question("Q1")], action="publish")
        survey = Survey.objects.get()
        Survey.objects.filter(pk=survey.pk).update(status=SurveyStatus.CLOSED)
        page = self.client.get(reverse("surveys:manage_edit", args=[survey.pk]))
        self.assertEqual(page.context["mode"], "readonly")
        self.assertContains(page, "chỉ xem được")
        self.assertNotContains(page, 'data-action="publish"')
