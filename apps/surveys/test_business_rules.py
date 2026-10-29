"""4.1.6 / 4.1.7 / 4.2.5 – quy tắc nghiệp vụ khảo sát: vòng đời, người nhận, quyền truy cập,
validation, chống gửi trùng và thống kê. Chạy trên test database (không đụng dữ liệu thật)."""
import json
import re
from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.constants import AccountStatus
from apps.accounts.models import Account
from apps.customers.models import Customer
from .models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient, SurveyResponse
from .questionnaire import NOT_USED
from .services import (build_stats, clone_survey, close_survey, send_survey, start_survey, submit_survey,
                       survey_overview)

PASSWORD = "SurveyRules!2026"
DT = "%Y-%m-%dT%H:%M"


# tv4: tạo khách hàng (tài khoản CUSTOMER + hồ sơ) cho test
def make_customer(email, **profile):
    account = Account.objects.create_user(email, PASSWORD)
    return Customer.objects.create(account=account, full_name=profile.pop("full_name", email), **profile)


# tv4: khung dữ liệu chung: 1 quản lý, 2 khách, 1 khảo sát nháp có câu một lựa chọn / nhiều lựa chọn / thang điểm
class SurveyFixture(TestCase):
    def setUp(self):
        self.manager = Account.objects.create_user("rules-manager@example.com", PASSWORD, role="MANAGER")
        self.an = make_customer("rules-an@example.com", full_name="An")
        self.binh = make_customer("rules-binh@example.com", full_name="Bình")
        now = timezone.now()
        self.survey = Survey.objects.create(title="Rules", status="DRAFT", created_by=self.manager,
                                            start_at=now - timedelta(hours=1), end_at=now + timedelta(days=7))
        self.single = SurveyQuestion.objects.create(survey=self.survey, question_text="Một", sort_order=1,
                                                    question_type="SINGLE_CHOICE", is_required=True)
        self.yes = SurveyOption.objects.create(question=self.single, option_text="Có", sort_order=1)
        self.no = SurveyOption.objects.create(question=self.single, option_text="Không", sort_order=2)
        self.multi = SurveyQuestion.objects.create(survey=self.survey, question_text="Nhiều", sort_order=2,
                                                   question_type="MULTI_CHOICE", config={"max_selections": 2})
        self.m = [SurveyOption.objects.create(question=self.multi, option_text=f"M{i}", sort_order=i) for i in range(1, 4)]
        self.rating = SurveyQuestion.objects.create(survey=self.survey, question_text="Điểm", sort_order=3,
                                                    question_type="RATING", config={"rating_min": 1, "rating_max": 5})

    # tv4: mời và phát hành cho danh sách khách
    def publish(self, *customers):
        send_survey(self.manager, self.survey, [c.pk for c in customers])
        self.survey.refresh_from_db()
        return {c.pk: SurveyRecipient.objects.get(survey=self.survey, customer=c) for c in customers}

    # tv4: bộ câu trả lời hợp lệ
    def answers(self, option=None, multi=(0,), score=4):
        rows = [{"question_id": self.single.pk, "option_id": (option or self.yes).pk}]
        rows += [{"question_id": self.multi.pk, "option_id": self.m[i].pk} for i in multi]
        if score is not None:
            rows.append({"question_id": self.rating.pk, "rating_value": score})
        return rows


# tv4: test vòng đời Nháp → Đang mở → Đã đóng và chọn người nhận
class LifecycleTests(SurveyFixture):
    def test_full_flow_create_invite_publish_answer_report(self):
        self.client.force_login(self.manager)
        start = timezone.localtime() - timedelta(minutes=5)
        response = self.client.post(reverse("surveys:manage_create"), {
            "title": "Luồng mới", "start_at": start.strftime(DT), "end_at": (start + timedelta(days=3)).strftime(DT),
            "objective": "SATISFACTION", "audience": "all"})
        survey = Survey.objects.get(title="Luồng mới")
        self.assertRedirects(response, reverse("surveys:manage_edit", args=[survey.pk]))  # lưu xong ở lại trình soạn
        self.assertEqual((survey.status, survey.template_key, survey.surveyquestion_set.count()), ("DRAFT", None, 0))
        self.client.post(reverse("surveys:manage_edit", args=[survey.pk]), {
            "title": "Luồng mới", "objective": "SATISFACTION", "audience": "all", "action": "save",
            "start_at": start.date().isoformat(), "end_at": (start + timedelta(days=3)).date().isoformat(),
            "questions_json": json.dumps([{"text": "Bạn hài lòng?", "type": "SINGLE_CHOICE", "required": True,
                                           "options": ["Có", "Không"]}])})
        question = survey.surveyquestion_set.get()
        self.client.post(reverse("surveys:manage_send", args=[survey.pk]),
                         {"audience": "pick", "customer_ids": [self.an.pk], "action": "send"})
        survey.refresh_from_db()
        self.assertEqual(survey.status, "ACTIVE")
        recipient = SurveyRecipient.objects.get(survey=survey)
        self.assertEqual(recipient.customer, self.an)

        self.client.force_login(self.an.account)
        self.assertContains(self.client.get(reverse("surveys:my_surveys")), "Luồng mới")
        self.assertEqual(self.client.get(reverse("surveys:take", args=[recipient.pk])).status_code, 200)
        yes = question.surveyoption_set.get(option_text="Có")
        response = self.client.post(reverse("surveys:submit", args=[recipient.pk]),
                                    {"answers": json.dumps([{"question_id": question.pk, "option_id": yes.pk}])},
                                    HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["submitted"])

        stats = build_stats(survey)
        self.assertEqual((stats["sent"], stats["done"], stats["pending"], stats["rate"], stats["responses"]),
                         (1, 1, 0, 100.0, 1))
        self.assertEqual([(r["label"], r["n"], r["pct"]) for r in stats["items"][0]["rows"]],
                         [("Có", 1, 100.0), ("Không", 0, 0.0)])
        self.client.force_login(self.manager)
        page = self.client.get(reverse("surveys:manage_stats", args=[survey.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context["stats"]["rate"], 100.0)

    def test_create_with_template_checkbox_creates_eight_questions(self):
        self.client.force_login(self.manager)
        start = timezone.localtime()
        self.client.post(reverse("surveys:manage_create"), {
            "title": "Mẫu", "start_at": start.strftime(DT), "end_at": (start + timedelta(days=3)).strftime(DT),
            "use_template": "on", "objective": "SATISFACTION", "audience": "all"})
        self.assertEqual(Survey.objects.get(title="Mẫu").surveyquestion_set.count(), 8)

    def test_publish_blocked_without_questions(self):
        empty = Survey.objects.create(title="Trống", status="DRAFT", created_by=self.manager,
                                      end_at=timezone.now() + timedelta(days=1))
        with self.assertRaises(ValidationError):
            send_survey(self.manager, empty, [self.an.pk])
        empty.refresh_from_db()
        self.assertEqual(empty.status, "DRAFT")
        self.assertFalse(SurveyRecipient.objects.filter(survey=empty).exists())

    def test_publish_blocked_without_recipients(self):
        with self.assertRaises(ValidationError):
            send_survey(self.manager, self.survey, [])
        Account.objects.filter(pk__in=[self.an.account_id, self.binh.account_id]).update(status=AccountStatus.LOCKED)
        self.client.force_login(self.manager)
        self.client.post(reverse("surveys:manage_send", args=[self.survey.pk]), {"audience": "all", "action": "send"})
        self.survey.refresh_from_db()
        self.assertEqual(self.survey.status, "DRAFT")
        self.assertFalse(SurveyRecipient.objects.exists())

    def test_publish_blocked_when_closed_or_expired(self):
        Survey.objects.filter(pk=self.survey.pk).update(end_at=timezone.now() - timedelta(minutes=1))
        self.survey.refresh_from_db()
        with self.assertRaises(ValidationError):
            send_survey(self.manager, self.survey, [self.an.pk])
        Survey.objects.filter(pk=self.survey.pk).update(status="CLOSED", end_at=timezone.now() + timedelta(days=1))
        with self.assertRaises(ValidationError):
            send_survey(self.manager, self.survey, [self.an.pk])

    def test_send_rejects_locked_or_deleted_and_never_duplicates(self):
        locked = make_customer("rules-locked@example.com")
        Account.objects.filter(pk=locked.account_id).update(status=AccountStatus.LOCKED)
        for customer_id in (locked.pk, 999999):
            with self.assertRaises(ValidationError):
                send_survey(self.manager, self.survey, [self.an.pk, customer_id])
        self.assertFalse(SurveyRecipient.objects.exists())  # cả lô bị từ chối, không ghi một phần
        self.assertEqual(send_survey(self.manager, self.survey, [self.an.pk, self.an.pk]), {"created": 1, "skipped": 0})
        self.assertEqual(send_survey(self.manager, self.survey, [self.an.pk, self.binh.pk]), {"created": 1, "skipped": 1})
        self.assertEqual(SurveyRecipient.objects.filter(survey=self.survey).count(), 2)

    def test_individual_pick_lists_only_eligible_customers(self):
        locked = make_customer("rules-locked2@example.com", full_name="Khóa")
        Account.objects.filter(pk=locked.account_id).update(status=AccountStatus.LOCKED)
        self.client.force_login(self.manager)
        page = self.client.get(reverse("surveys:manage_send", args=[self.survey.pk]))
        self.assertContains(page, "rules-an@example.com")
        self.assertNotContains(page, "rules-locked2@example.com")
        self.client.post(reverse("surveys:manage_send", args=[self.survey.pk]),
                         {"audience": "pick", "customer_ids": [locked.pk], "action": "send"})
        self.assertFalse(SurveyRecipient.objects.exists())

    def test_questions_locked_after_publish_and_answers(self):
        recipients = self.publish(self.an)
        submit_survey(self.an.account, recipients[self.an.pk].pk, self.answers())
        self.client.force_login(self.manager)
        today = timezone.localdate()
        self.client.post(reverse("surveys:manage_edit", args=[self.survey.pk]), {
            "title": "Đổi", "objective": "OTHER", "audience": "all", "action": "save",
            "start_at": today.isoformat(), "end_at": today.isoformat(),
            "questions_json": json.dumps([{"text": "Đổi", "type": "SINGLE_CHOICE", "options": ["A", "B"]}])})
        self.single.refresh_from_db()
        self.assertEqual(self.single.question_text, "Một")
        self.assertEqual(list(self.single.surveyoption_set.values_list("option_text", flat=True)), ["Có", "Không"])

    def test_manual_close_and_clone_copy_questions_only(self):
        recipients = self.publish(self.an)
        submit_survey(self.an.account, recipients[self.an.pk].pk, self.answers())
        close_survey(self.manager, self.survey)
        self.assertEqual(Survey.objects.get(pk=self.survey.pk).status, "CLOSED")
        self.multi.config["other_option_id"] = self.m[2].pk
        self.multi.save()
        copy = clone_survey(self.manager, self.survey)
        self.assertEqual((copy.status, copy.surveyrecipient_set.count()), ("DRAFT", 0))
        copied = list(copy.surveyquestion_set.order_by("sort_order"))
        self.assertEqual([q.question_text for q in copied], ["Một", "Nhiều", "Điểm"])
        other = copied[1].config["other_option_id"]
        self.assertEqual(SurveyOption.objects.get(pk=other).question, copied[1])
        self.assertEqual(SurveyAnswer.objects.filter(question__survey=copy).count(), 0)

    def test_close_draft_is_rejected(self):
        with self.assertRaises(ValidationError):
            close_survey(self.manager, self.survey)


# tv4: test khách chỉ truy cập được khảo sát được mời, đã phát hành, còn hạn, tài khoản không khóa
class CustomerAccessTests(SurveyFixture):
    def setUp(self):
        super().setUp()
        self.recipients = self.publish(self.an, self.binh)
        self.mine = self.recipients[self.an.pk]

    # tv4: GET take và POST submit đều bị từ chối, không lưu câu trả lời
    def assert_denied(self, recipient, user):
        self.client.force_login(user)
        take = self.client.get(reverse("surveys:take", args=[recipient.pk]))
        submit = self.client.post(reverse("surveys:submit", args=[recipient.pk]), {"answers": json.dumps(self.answers())})
        self.assertIn(take.status_code, (400, 403))
        self.assertIn(submit.status_code, (400, 403))
        self.assertFalse(SurveyResponse.objects.filter(recipient=recipient, status="SUBMITTED").exists())

    def test_other_customers_invitation_is_forbidden(self):
        self.client.force_login(self.an.account)
        other = self.recipients[self.binh.pk]
        self.assertEqual(self.client.get(reverse("surveys:take", args=[other.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("surveys:result", args=[other.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("surveys:submit", args=[other.pk]),
                                          {"answers": json.dumps(self.answers())}).status_code, 403)

    def test_uninvited_customer_sees_nothing(self):
        stranger = make_customer("rules-stranger@example.com")
        self.client.force_login(stranger.account)
        self.assertNotContains(self.client.get(reverse("surveys:my_surveys")), "Rules")
        self.assert_denied(self.mine, stranger.account)

    def test_draft_survey_is_never_exposed(self):
        Survey.objects.filter(pk=self.survey.pk).update(status="DRAFT")
        self.client.force_login(self.an.account)
        self.assertNotContains(self.client.get(reverse("surveys:my_surveys")), "Rules")
        self.assert_denied(self.mine, self.an.account)

    def test_closed_survey_is_rejected(self):
        Survey.objects.filter(pk=self.survey.pk).update(status="CLOSED")
        self.assert_denied(self.mine, self.an.account)

    def test_expired_survey_is_rejected(self):
        Survey.objects.filter(pk=self.survey.pk).update(end_at=timezone.now() - timedelta(seconds=1))
        self.assert_denied(self.mine, self.an.account)

    def test_not_yet_open_survey_is_rejected_and_labelled(self):
        Survey.objects.filter(pk=self.survey.pk).update(start_at=timezone.now() + timedelta(days=1))
        self.client.force_login(self.an.account)
        self.assertContains(self.client.get(reverse("surveys:my_surveys")), "Chưa đến thời gian mở")
        self.assert_denied(self.mine, self.an.account)

    def test_locked_account_is_rejected(self):
        Account.objects.filter(pk=self.an.account_id).update(status=AccountStatus.LOCKED)
        self.assert_denied(self.mine, self.an.account)
        self.an.account.refresh_from_db()
        with self.assertRaises(PermissionDenied):  # gọi service trực tiếp cũng bị chặn
            submit_survey(self.an.account, self.mine.pk, self.answers())

    def test_customer_cannot_open_management(self):
        self.client.force_login(self.an.account)
        for name, args in (("surveys:manage_list", []), ("surveys:manage_stats", [self.survey.pk]),
                           ("surveys:manage_send", [self.survey.pk])):
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 302)
            self.assertNotIn("/surveys/manage", response.url)
        self.client.post(reverse("surveys:manage_close", args=[self.survey.pk]))
        self.assertEqual(Survey.objects.get(pk=self.survey.pk).status, "ACTIVE")

    def test_manager_cannot_answer_as_customer(self):
        with self.assertRaises(PermissionDenied):
            start_survey(self.manager, self.mine.pk)

    def test_two_submissions_store_one_response(self):
        self.client.force_login(self.an.account)
        url = reverse("surveys:submit", args=[self.mine.pk])
        first = self.client.post(url, {"answers": json.dumps(self.answers())}, HTTP_ACCEPT="application/json")
        second = self.client.post(url, {"answers": json.dumps(self.answers(option=self.no))}, HTTP_ACCEPT="application/json")
        self.assertTrue(first.json()["submitted"])
        self.assertFalse(second.json()["submitted"])
        self.assertEqual(SurveyResponse.objects.filter(recipient=self.mine).count(), 1)
        self.assertEqual(SurveyAnswer.objects.get(question=self.single).option, self.yes)


# tv4: test validation câu trả lời ở backend
class ValidationTests(SurveyFixture):
    def setUp(self):
        super().setUp()
        self.mine = self.publish(self.an)[self.an.pk]

    # tv4: nộp payload sai → lỗi 400 JSON và không lưu gì
    def assert_rejected(self, payload):
        self.client.force_login(self.an.account)
        response = self.client.post(reverse("surveys:submit", args=[self.mine.pk]),
                                    {"answers": json.dumps(payload)}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.json()["errors"])
        self.assertFalse(SurveyAnswer.objects.exists())
        self.assertFalse(SurveyResponse.objects.filter(status="SUBMITTED").exists())

    def test_missing_required_question(self):
        self.assert_rejected([{"question_id": self.rating.pk, "rating_value": 3}])

    def test_option_from_another_question(self):
        self.assert_rejected([{"question_id": self.single.pk, "option_id": self.m[0].pk}])

    def test_single_choice_accepts_exactly_one(self):
        self.assert_rejected(self.answers() + [{"question_id": self.single.pk, "option_id": self.no.pk}])

    def test_multi_choice_over_limit(self):
        self.assert_rejected(self.answers(multi=(0, 1, 2)))

    def test_rating_outside_scale(self):
        for score in (0, 6):
            self.assert_rejected(self.answers(score=score))

    def test_text_too_long(self):
        text = SurveyQuestion.objects.create(survey=self.survey, question_text="Ý kiến", question_type="TEXT", sort_order=4)
        self.assert_rejected(self.answers() + [{"question_id": text.pk, "answer_text": "x" * 2001}])

    def test_valid_answer_is_saved(self):
        self.assertTrue(submit_survey(self.an.account, self.mine.pk, self.answers(multi=(0, 1))))
        self.assertEqual(SurveyAnswer.objects.count(), 4)


# tv4: test thống kê 4.1.7 – rỗng, chọn nhiều > 100%, ma trận loại "Không sử dụng", tổng quan
class StatisticsTests(SurveyFixture):
    def test_empty_survey_has_no_fake_percentages(self):
        stats = build_stats(self.survey)
        self.assertEqual((stats["sent"], stats["rate"]), (0, None))
        self.assertTrue(all(item["no_data"] for item in stats["items"]))
        self.assertTrue(all(row["pct"] is None for item in stats["items"] for row in item["rows"]))
        self.client.force_login(self.manager)
        page = self.client.get(reverse("surveys:manage_stats", args=[self.survey.pk])).content.decode()
        self.assertTrue("Chưa có dữ liệu" in page or "No data yet" in page)
        self.assertIsNone(re.search(r"(?<![\d.,])0([.,]0)?\s*%", page))  # không có "0%" giả
        self.assertNotIn("NaN", page)
        self.assertNotIn("None", page)

    def test_multi_choice_can_exceed_100_percent_and_rating_average(self):
        recipients = self.publish(self.an, self.binh)
        submit_survey(self.an.account, recipients[self.an.pk].pk, self.answers(multi=(0, 1), score=5))
        submit_survey(self.binh.account, recipients[self.binh.pk].pk, self.answers(option=self.no, multi=(0,), score=2))
        items = {i["question"].pk: i for i in build_stats(self.survey)["items"]}
        multi = items[self.multi.pk]
        self.assertEqual([r["pct"] for r in multi["rows"]], [100.0, 50.0, 0.0])
        self.assertGreater(sum(r["pct"] for r in multi["rows"]), 100)
        self.assertEqual(items[self.rating.pk]["avg"], 3.5)
        self.assertEqual([r["n"] for r in items[self.rating.pk]["rows"]], [0, 1, 0, 0, 1])

    def test_matrix_not_used_is_excluded_from_average(self):
        matrix = SurveyQuestion.objects.create(survey=self.survey, question_text="Tiêu chí", question_type="MATRIX",
                                               sort_order=4)
        price = SurveyOption.objects.create(question=matrix, option_text="Giá", sort_order=1)
        recipients = self.publish(self.an, self.binh)
        submit_survey(self.an.account, recipients[self.an.pk].pk,
                      self.answers() + [{"question_id": matrix.pk, "option_id": price.pk, "rating_value": 4}])
        submit_survey(self.binh.account, recipients[self.binh.pk].pk,
                      self.answers() + [{"question_id": matrix.pk, "option_id": price.pk, "answer_text": NOT_USED}])
        criterion = next(i for i in build_stats(self.survey)["items"] if i["question"] == matrix)["criteria"][0]
        self.assertEqual((criterion["avg"], criterion["scored"], criterion["not_used"]), (4, 1, 1))

    def test_overview_counts_only_published_surveys(self):
        self.assertEqual(survey_overview(), {"published": 0, "responses": 0, "invited": 0, "done": 0, "rate": None})
        recipients = self.publish(self.an, self.binh)
        submit_survey(self.an.account, recipients[self.an.pk].pk, self.answers())
        Survey.objects.create(title="Nháp khác", status="DRAFT", created_by=self.manager)
        overview = survey_overview()
        self.assertEqual((overview["published"], overview["responses"], overview["rate"]), (1, 1, 50.0))
        self.client.force_login(self.manager)
        page = self.client.get(reverse("surveys:manage_list"))
        self.assertEqual(page.context["overview"]["rate"], 50.0)
        listed = {s.pk: s for s in page.context["surveys"]}[self.survey.pk]
        self.assertEqual((listed.pending, listed.rate), (1, 50.0))
        self.assertEqual(listed.status_label, "Open")  # MANAGER xem Manager Portal bằng tiếng Anh, không còn mã thô

    def test_answers_of_later_locked_customer_still_count(self):
        recipients = self.publish(self.an)
        submit_survey(self.an.account, recipients[self.an.pk].pk, self.answers())
        Account.objects.filter(pk=self.an.account_id).update(status=AccountStatus.LOCKED)
        self.assertEqual(build_stats(self.survey)["responses"], 1)
