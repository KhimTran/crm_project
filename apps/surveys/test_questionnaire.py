"""The versioned questionnaire's storage, validation and report contract."""
import json
from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth.models import Group
from django.db import DatabaseError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.customers.models import Customer
from .configuration import populate_questionnaire
from .forms import QuestionForm
from .models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient, SurveyResponse
from .questionnaire import NOT_USED, SECTIONS, TEMPLATE_KEY
from .services import build_stats, submit_survey


class QuestionnaireTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@questionnaire.test", "SurveyFixture!2026", role="MANAGER")
        cls.customers = [Customer.objects.create(
            account=Account.objects.create_user(f"customer{i}@questionnaire.test", "SurveyFixture!2026"),
            full_name=f"Survey Customer {i}") for i in range(2)]

    def setUp(self):
        self.survey = Survey.objects.create(title="Eight questions", status="DRAFT", created_by=self.manager,
            start_at=timezone.now() - timedelta(days=1), end_at=timezone.now() + timedelta(days=7))
        populate_questionnaire(self.survey)
        self.questions = list(self.survey.surveyquestion_set.order_by("sort_order"))
        self.by_key = {q.config["key"]: q for q in self.questions}
        self.options = {q.pk: list(q.surveyoption_set.order_by("sort_order")) for q in self.questions}
        self.survey.status = "ACTIVE"
        self.survey.save(update_fields=["status"])
        self.recipients = [SurveyRecipient.objects.create(survey=self.survey, customer=c, status="SENT")
                           for c in self.customers]

    def payload(self):
        answers = []
        for q in self.questions:
            if q.question_type in ("SINGLE_CHOICE", "MULTI_CHOICE"):
                selected = self.options[q.pk][:2 if q.question_type == "MULTI_CHOICE" else 1]
                answers.extend({"question_id": q.pk, "option_id": o.pk} for o in selected)
            elif q.question_type == "RATING":
                answers.append({"question_id": q.pk, "rating_value": q.config["rating_max"]})
            elif q.question_type == "MATRIX":
                for i, o in enumerate(self.options[q.pk]):
                    answers.append({"question_id": q.pk, "option_id": o.pk,
                        **({"answer_text": NOT_USED} if i == 1 else {"rating_value": 4})})
        return answers

    def assert_rejected(self, answers):
        with self.assertRaises(ValidationError):
            submit_survey(self.customers[0].account, self.recipients[0].pk, answers)
        self.assertFalse(SurveyAnswer.objects.exists())
        self.assertFalse(SurveyResponse.objects.exists())

    def test_manager_create_stores_eight_questions_and_three_sections(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("surveys:manage_create"), {
            "title": "New version", "start_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
            "end_at": (timezone.localtime() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M"), "use_template": "on",
            "objective": "SATISFACTION", "audience": "all"})
        self.assertEqual(response.status_code, 302)
        survey = Survey.objects.get(title="New version")
        self.assertEqual(survey.template_key, TEMPLATE_KEY)
        questions = list(survey.surveyquestion_set.order_by("sort_order"))
        self.assertEqual(len(questions), 8)
        self.assertEqual([q.sort_order for q in questions], list(range(1, 9)))
        self.assertEqual(list(dict.fromkeys(q.config["section"] for q in questions)), list(SECTIONS))
        self.assertTrue(all(q.is_required for q in questions[:7]))
        self.assertFalse(questions[7].is_required)
        self.assertEqual(questions[4].config["max_selections"], 3)
        self.assertEqual(questions[6].config["rating_max"], 10)
        self.assertEqual(self.survey.surveyquestion_set.count(), 8)

    def test_valid_answers_distinct_matrix_states_optional_text_and_repeat_submit(self):
        answers = self.payload()
        suggestions = self.by_key["suggestions"]
        answers.append({"question_id": suggestions.pk, "answer_text": "   "})
        self.assertTrue(submit_survey(self.customers[0].account, self.recipients[0].pk, answers))
        self.assertFalse(SurveyAnswer.objects.filter(question=suggestions).exists())
        unused = SurveyAnswer.objects.get(answer_text=NOT_USED)
        self.assertIsNone(unused.rating_value)
        self.assertEqual(SurveyAnswer.objects.get(question=self.by_key["recommendation"]).rating_value, 10)
        count = SurveyAnswer.objects.count()
        self.assertFalse(submit_survey(self.customers[0].account, self.recipients[0].pk, answers))
        self.assertEqual(SurveyAnswer.objects.count(), count)
        self.assertEqual(SurveyResponse.objects.count(), 1)

    def test_max_three_and_integral_one_to_ten_are_enforced_by_server(self):
        highlights = self.by_key["highlights"]
        answers = [a for a in self.payload() if a["question_id"] != highlights.pk]
        answers += [{"question_id": highlights.pk, "option_id": o.pk} for o in self.options[highlights.pk][:4]]
        self.assert_rejected(answers)
        recommendation = self.by_key["recommendation"]
        for score in (0, 11, 1.5, True, "7"):
            with self.subTest(score=score):
                answers = self.payload()
                next(a for a in answers if a["question_id"] == recommendation.pk)["rating_value"] = score
                self.assert_rejected(answers)
        # One highlight is sufficient; choosing all three is not required.
        answers = self.payload()
        answers.remove(next(a for a in reversed(answers) if a["question_id"] == highlights.pk))
        self.assertTrue(submit_survey(self.customers[0].account, self.recipients[0].pk, answers))

    def test_other_requires_text_and_rejects_stale_text_on_another_option(self):
        brands = self.by_key["future_brands"]
        for text in (None, "  ", "x" * 201):
            answers = self.payload() + [{"question_id": brands.pk, "option_id": brands.config["other_option_id"]}]
            if text is not None:
                answers[-1]["answer_text"] = text
            self.assert_rejected(answers)
        answers = self.payload()
        next(a for a in answers if a["question_id"] == brands.pk)["answer_text"] = "Stale Other"
        self.assert_rejected(answers)
        answers = self.payload() + [{"question_id": brands.pk, "option_id": brands.config["other_option_id"],
                                    "answer_text": "  Felet  "}]
        self.assertTrue(submit_survey(self.customers[0].account, self.recipients[0].pk, answers))
        self.assertEqual(SurveyAnswer.objects.get(answer_text="Felet").option_id, brands.config["other_option_id"])

    def test_matrix_rejects_missing_duplicate_foreign_and_ambiguous_criteria(self):
        matrix = self.by_key["service_criteria"]
        base = self.payload()
        row = next(i for i, a in enumerate(base) if a["question_id"] == matrix.pk)
        missing = deepcopy(base)
        missing.pop(row)
        self.assert_rejected(missing)
        self.assert_rejected(base + [base[row]])
        for patch_values in ({"rating_value": 0}, {"answer_text": NOT_USED},
                             {"option_id": self.options[self.by_key["purchases"].pk][0].pk}):
            answers = deepcopy(base)
            answers[row].update(patch_values)
            self.assert_rejected(answers)

    def test_reports_use_correct_denominators_matrix_averages_and_escaped_text(self):
        matrix, highlights = self.by_key["service_criteria"], self.by_key["highlights"]
        for q in (matrix, highlights):
            SurveyQuestion.objects.filter(pk=q.pk).update(is_required=False)
        first = self.payload()
        brands = self.by_key["future_brands"]
        first.append({"question_id": brands.pk, "option_id": brands.config["other_option_id"], "answer_text": "<script>Other</script>"})
        submit_survey(self.customers[0].account, self.recipients[0].pk, first)
        second = [a for a in self.payload() if a["question_id"] not in (matrix.pk, highlights.pk)]
        second.append({"question_id": matrix.pk, "option_id": self.options[matrix.pk][0].pk, "rating_value": 2})
        next(a for a in second if a["question_id"] == self.by_key["overall_satisfaction"].pk)["rating_value"] = 3
        next(a for a in second if a["question_id"] == self.by_key["recommendation"].pk)["rating_value"] = 1
        second.append({"question_id": self.by_key["suggestions"].pk, "answer_text": "Better packaging"})
        submit_survey(self.customers[1].account, self.recipients[1].pk, second)
        stats = build_stats(self.survey)
        by_key = {i["question"].config["key"]: i for i in stats["items"]}
        self.assertEqual((stats["sent"], stats["done"]), (2, 2))
        self.assertEqual(by_key["highlights"]["respondents"], 1)
        self.assertEqual([r["pct"] for r in by_key["highlights"]["rows"][:2]], [100, 100])
        self.assertEqual(by_key["overall_satisfaction"]["avg"], 4)
        criterion = by_key["service_criteria"]["criteria"]
        self.assertEqual(criterion[0]["avg"], 3)
        self.assertEqual((criterion[1]["not_used"], criterion[1]["unanswered"], criterion[1]["avg"]), (1, 1, None))
        self.assertEqual(len(by_key["recommendation"]["rows"]), 10)
        self.assertEqual(by_key["recommendation"]["avg"], 5.5)  # thang điểm 1–10: phân bố + trung bình
        self.assertEqual(by_key["suggestions"]["respondents"], 1)
        self.client.force_login(self.manager)
        for url in (reverse("surveys:manage_stats", args=[self.survey.pk]),
                    reverse("surveys:results") + f"?survey_id={self.survey.pk}"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "100.0%")
            self.assertContains(response, "&lt;script&gt;Other&lt;/script&gt;")
            self.assertNotContains(response, "<script>Other</script>")
        # The Survey statistics page shows the raw 1–10 distribution only; NPS lives in Survey Results.
        self.assertNotContains(self.client.get(reverse("surveys:manage_stats", args=[self.survey.pk])), "NPS")

    def test_legacy_surveys_keep_one_to_five_and_are_not_relabelled(self):
        legacy = Survey.objects.create(title="Legacy", status="ACTIVE", created_by=self.manager)
        question = SurveyQuestion.objects.create(survey=legacy, question_text="Old rating", question_type="RATING")
        recipient = SurveyRecipient.objects.create(survey=legacy, customer=self.customers[0], status="SENT")
        with self.assertRaises(ValidationError):
            submit_survey(self.customers[0].account, recipient.pk, [{"question_id": question.pk, "rating_value": 6}])
        submit_survey(self.customers[0].account, recipient.pk, [{"question_id": question.pk, "rating_value": 5}])
        before = list(SurveyAnswer.objects.values())
        with self.assertRaises(ValidationError):
            populate_questionnaire(legacy)
        legacy.refresh_from_db()
        self.assertIsNone(legacy.template_key)
        self.assertEqual(list(SurveyAnswer.objects.values()), before)
        self.assertEqual(build_stats(legacy)["items"][0]["avg"], 5)
        self.assertEqual(build_stats(self.survey)["items"][0]["respondents"], 0)

    def test_json_submission_errors_csrf_and_ownership(self):
        url = reverse("surveys:submit", args=[self.recipients[0].pk])
        self.client.force_login(self.customers[0].account)
        response = self.client.post(url, {"answers": "[]"}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        with patch("apps.surveys.views.submit_survey", side_effect=DatabaseError("private details")):
            response = self.client.post(url, {"answers": json.dumps(self.payload())}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private details", response.content.decode())
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.customers[0].account)
        self.assertEqual(csrf_client.post(url, {"answers": "[]"}, HTTP_ACCEPT="application/json").status_code, 403)
        with self.assertRaises(PermissionDenied):
            submit_survey(self.customers[1].account, self.recipients[0].pk, self.payload())
        self.assertFalse(SurveyAnswer.objects.exists())

    def test_configuration_edit_and_fixed_order_preserve_the_version(self):
        # A distinct empty draft has no recipients/answers and is safely editable.
        draft = Survey.objects.create(title="Draft", status="DRAFT", created_by=self.manager)
        populate_questionnaire(draft)
        question = draft.surveyquestion_set.get(config__key="highlights")
        form = QuestionForm({"question_text": question.question_text, "options_text": "\n".join(
            question.surveyoption_set.order_by("sort_order").values_list("option_text", flat=True))}, instance=question)
        self.assertTrue(form.is_valid(), form.errors)
        form.save_for(draft)
        question.refresh_from_db()
        self.assertFalse(question.is_required)
        self.assertEqual(question.config["max_selections"], 3)
        self.client.force_login(self.manager)
        # trình soạn: bộ 8 câu không thêm/bớt câu được; sửa nội dung thì giữ loại câu, cấu hình và thứ tự
        url = reverse("surveys:manage_edit", args=[draft.pk])
        page = self.client.get(url)
        self.assertEqual(page.context["mode"], "fixed")
        items = page.context["builder_items"]
        today = timezone.localdate()
        base = {"title": "Draft", "objective": "SATISFACTION", "audience": "all", "action": "save",
                "start_at": today.isoformat(), "end_at": today.isoformat()}
        response = self.client.post(url, {**base, "questions_json": json.dumps(items[:7])})
        self.assertContains(response, "The fixed questionnaire must keep all of its questions and their order.")
        self.assertEqual(draft.surveyquestion_set.count(), 8)
        items[0]["text"] = "Câu 1 đã sửa"
        items[4]["options"][0] = "Hàng chính hãng 100%."
        response = self.client.post(url, {**base, "questions_json": json.dumps(items)})
        self.assertRedirects(response, url, fetch_redirect_response=False)
        rows = list(draft.surveyquestion_set.order_by("sort_order"))
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[0].question_text, "Câu 1 đã sửa")
        self.assertEqual((rows[4].config["key"], rows[4].config["max_selections"]), ("highlights", 3))
        self.assertEqual(rows[4].surveyoption_set.order_by("sort_order").first().option_text, "Hàng chính hãng 100%.")
        brands = rows[5]
        self.assertEqual(brands.surveyoption_set.get(pk=brands.config["other_option_id"]).option_text, "Khác.")
        items[3]["type"] = "TEXT"  # đổi loại câu bị server từ chối
        response = self.client.post(url, {**base, "questions_json": json.dumps(items)})
        self.assertIn("3", response.context["builder"]["errors"])

    def test_customer_service_opens_report_without_survey_results(self):
        staff = Account.objects.create_user("staff@questionnaire.test", "SurveyFixture!2026")
        staff.groups.add(Group.objects.get_or_create(name="CUSTOMER_SERVICE")[0])
        self.client.force_login(staff)
        response = self.client.get(reverse("surveys:results"), {"survey_id": self.survey.pk})
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(self.client.get(reverse("customer_reports:customers")).status_code, 200)
