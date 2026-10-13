"""PR #6 type, atomicity, navigation and localized statistics regressions."""
import json
from copy import deepcopy

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import Account
from apps.customers.models import Customer
from .models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient, SurveyResponse
from .services import build_stats, submit_survey


class SurveyRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Account.objects.create_superuser("pr6-admin@example.test", "StrongPass!2026")
        cls.account = Account.objects.create_user("pr6-customer@example.test", "StrongPass!2026")
        cls.customer = Customer.objects.create(account=cls.account, full_name="Survey regression customer")
        cls.survey = Survey.objects.create(title="Four types", status="ACTIVE", created_by=cls.admin)
        cls.questions = [SurveyQuestion.objects.create(
            survey=cls.survey, question_text=kind, question_type=kind, is_required=True, sort_order=i,
        ) for i, kind in enumerate(("TEXT", "RATING", "SINGLE_CHOICE", "MULTI_CHOICE"))]
        cls.text, cls.rating, cls.single, cls.multi = cls.questions
        cls.single_options = [SurveyOption.objects.create(question=cls.single, option_text=value) for value in ("A", "B")]
        cls.multi_options = [SurveyOption.objects.create(question=cls.multi, option_text=value) for value in ("C", "D")]
        cls.recipient = SurveyRecipient.objects.create(survey=cls.survey, customer=cls.customer, status="SENT")

    def answers(self):
        return [
            {"question_id": self.text.pk, "answer_text": "  Useful text  "},
            {"question_id": self.rating.pk, "rating_value": 4},
            {"question_id": self.single.pk, "option_id": self.single_options[0].pk},
            {"question_id": self.multi.pk, "option_id": self.multi_options[0].pk},
            {"question_id": self.multi.pk, "option_id": self.multi_options[1].pk},
        ]

    def assert_rejected(self, answers):
        with self.assertRaises(ValidationError):
            submit_survey(self.account, self.recipient.pk, answers)
        self.assertFalse(SurveyAnswer.objects.exists())
        self.assertFalse(SurveyResponse.objects.exists())
        self.recipient.refresh_from_db()
        self.assertEqual(self.recipient.status, "SENT")
        self.assertIsNone(self.recipient.completed_at)

    def test_text_requires_a_nonempty_string_after_strip(self):
        for value in (None, "", " \n\t ", True, 123, [], {}):
            with self.subTest(value=value):
                answers = self.answers()
                answers[0]["answer_text"] = value
                self.assert_rejected(answers)

    def test_rating_requires_an_integer_from_one_to_five(self):
        for value in (None, True, False, "4", "4.5", 4.0, 4.5, 0, 6, -1, [], {}):
            with self.subTest(value=value):
                answers = self.answers()
                answers[1]["rating_value"] = value
                self.assert_rejected(answers)
        for value in range(1, 6):
            # Each customer has their own submission, including both boundaries.
            account = Account.objects.create_user(f"rating-{value}@example.test", "StrongPass!2026")
            customer = Customer.objects.create(account=account, full_name=f"Rating {value}")
            recipient = SurveyRecipient.objects.create(survey=self.survey, customer=customer, status="SENT")
            answers = self.answers()
            answers[1]["rating_value"] = value
            self.assertTrue(submit_survey(account, recipient.pk, answers))
            self.assertEqual(SurveyAnswer.objects.get(response__recipient=recipient, question=self.rating).rating_value, value)

    def test_choices_require_integer_options_from_the_correct_question(self):
        for index, foreign_option in ((2, self.multi_options[0].pk), (3, self.single_options[0].pk)):
            for value in (None, True, "1", 1.0, [], {}, 0, 2147483648, foreign_option, 999999):
                with self.subTest(index=index, value=value):
                    answers = self.answers()
                    answers[index]["option_id"] = value
                    self.assert_rejected(answers)

    def test_each_type_rejects_mixed_and_unknown_fields_even_if_null(self):
        extra_fields = (
            {"option_id": self.single_options[0].pk, "rating_value": 5},
            {"answer_text": "not a rating", "option_id": self.single_options[0].pk},
            {"answer_text": "not a choice", "rating_value": 5},
            {"answer_text": "not a choice", "rating_value": 5},
        )
        for index, fields in enumerate(extra_fields):
            for field, value in {**fields, "unknown": "x"}.items():
                for extra in (value, None):
                    with self.subTest(index=index, field=field, value=extra):
                        answers = self.answers()
                        answers[index][field] = extra
                        self.assert_rejected(answers)

    def test_malformed_payloads_and_question_identifiers_are_validation_errors(self):
        for payload in (None, {}, "text", 4, [None], [True], ["text"], [{}]):
            with self.subTest(payload=payload):
                self.assert_rejected(payload)
        for value in (None, True, "1", 1.5, [], {}, -1, 2147483648, 999999):
            with self.subTest(question_id=value):
                answers = self.answers()
                answers[0]["question_id"] = value
                self.assert_rejected(answers)

    def test_duplicates_missing_required_fields_and_foreign_questions_are_rejected(self):
        self.assert_rejected(self.answers() + [self.answers()[0]])
        self.assert_rejected(self.answers() + [self.answers()[3]])
        for index, field in ((0, "answer_text"), (1, "rating_value"), (2, "option_id")):
            answers = self.answers()
            del answers[index][field]
            self.assert_rejected(answers)
        self.assert_rejected(self.answers()[1:])
        other = Survey.objects.create(title="Other", status="ACTIVE", created_by=self.admin)
        question = SurveyQuestion.objects.create(survey=other, question_text="Foreign", question_type="TEXT")
        self.assert_rejected(self.answers() + [{"question_id": question.pk, "answer_text": "x"}])

    def test_valid_types_strip_text_and_keep_one_submission(self):
        answers = self.answers()
        original = deepcopy(answers)
        self.assertTrue(submit_survey(self.account, self.recipient.pk, answers))
        self.assertEqual(answers, original)
        self.assertEqual(SurveyAnswer.objects.get(question=self.text).answer_text, "Useful text")
        self.assertEqual(SurveyAnswer.objects.count(), 5)
        self.assertFalse(submit_survey(self.account, self.recipient.pk, answers))
        self.assertEqual(SurveyAnswer.objects.count(), 5)
        self.assertEqual(SurveyResponse.objects.count(), 1)

    def test_optional_questions_can_be_omitted_but_submitted_blank_text_is_rejected(self):
        SurveyQuestion.objects.filter(pk=self.text.pk).update(is_required=False)
        answers = self.answers()
        answers[0]["answer_text"] = "  "
        self.assert_rejected(answers)
        self.assertTrue(submit_survey(self.account, self.recipient.pk, self.answers()[1:]))

    def test_http_invalid_answers_return_400_without_partial_writes(self):
        self.client.force_login(self.account)
        url = reverse("surveys:submit", args=[self.recipient.pk])
        for payload in ([None], [{"question_id": True}], {"question_id": 1}, self.answers()[:1]):
            response = self.client.post(url, {"answers": json.dumps(payload)})
            self.assertEqual(response.status_code, 400)
        answers = self.answers()
        answers[1]["rating_value"] = 4.5
        self.assertEqual(self.client.post(url, {"answers": json.dumps(answers)}).status_code, 400)
        self.assertFalse(SurveyAnswer.objects.exists())
        self.assertFalse(SurveyResponse.objects.exists())

    def test_closed_survey_rejects_http_submission(self):
        Survey.objects.filter(pk=self.survey.pk).update(status="CLOSED")
        self.client.force_login(self.account)
        url = reverse("surveys:submit", args=[self.recipient.pk])
        self.assertEqual(self.client.post(url, {"answers": json.dumps(self.answers())}).status_code, 400)
        self.assertFalse(SurveyAnswer.objects.exists())

    @override_settings(LANGUAGE_CODE="vi")
    def test_statistics_keep_decimal_points_in_css_and_correct_counts(self):
        for index in range(3):
            if index == 0:
                account, recipient = self.account, self.recipient
            else:
                account = Account.objects.create_user(f"stats-{index}@example.test", "StrongPass!2026")
                customer = Customer.objects.create(account=account, full_name=f"Stats {index}")
                recipient = SurveyRecipient.objects.create(survey=self.survey, customer=customer, status="SENT")
            answers = self.answers()
            answers[1]["rating_value"] = index + 3
            answers[2]["option_id"] = self.single_options[0 if index < 2 else 1].pk
            submit_survey(account, recipient.pk, answers)
        stats = build_stats(self.survey)
        self.assertEqual((stats["sent"], stats["done"], stats["pending"], stats["rate"]), (3, 3, 0, 100.0))
        by_type = {item["question"].question_type: item for item in stats["items"]}
        self.assertEqual(by_type["RATING"]["avg"], 4.0)
        self.assertEqual(by_type["SINGLE_CHOICE"]["rows"][0]["pct"], 66.7)
        self.assertEqual(by_type["MULTI_CHOICE"]["respondents"], 3)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("surveys:manage_stats", args=[self.survey.pk]))
        self.assertContains(response, 'style="width:66.7%"')
        self.assertNotContains(response, 'style="width:66,7%"')

    def test_customer_crm_and_admin_menus_preserve_integrated_routes(self):
        self.client.force_login(self.account)
        for path in ("/", reverse("surveys:my_surveys"), reverse("feedbacks:mine")):
            response = self.client.get(path)
            for asset in ("/static/css/tv1.css", "/static/vendor/bootstrap.min.css"):
                self.assertContains(response, asset)
            for route in ("feedbacks:mine", "surveys:my_surveys", "shop:products"):
                self.assertContains(response, f'href="{reverse(route)}"')
        self.client.force_login(self.admin)
        response = self.client.get(reverse("surveys:manage_list"))
        for route in ("crm_feedbacks:list", "surveys:manage_list", "customers:list", "customer_auth:logout"):
            self.assertContains(response, reverse(route))
        for route in ("catalog_admin:category_list", "catalog_admin:brand_list"):
            response = self.client.get(reverse(route))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f'href="{reverse("catalog_admin:category_list")}"')
            self.assertContains(response, f'href="{reverse("catalog_admin:brand_list")}"')
            self.assertContains(response, f'href="{reverse("surveys:manage_list")}"')
