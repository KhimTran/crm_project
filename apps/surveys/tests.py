import json

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.customers.models import Customer
from .models import Survey, SurveyAnswer, SurveyOption, SurveyQuestion, SurveyRecipient, SurveyResponse
from .services import send_survey, submit_survey


class SurveyUniquenessTests(TestCase):
    def setUp(self):
        model = get_user_model()
        self.admin = model.objects.create_superuser("survey-admin@example.com", "StrongPass!2026")
        self.account = model.objects.create_user("survey-customer@example.com", "StrongPass!2026")
        self.customer = Customer.objects.create(account=self.account, full_name="Demo customer")
        self.survey = Survey.objects.create(title="Demo", status="ACTIVE", created_by=self.admin)
        self.question = SurveyQuestion.objects.create(survey=self.survey, question_text="Choose", question_type="SINGLE_CHOICE", is_required=True)
        self.option = SurveyOption.objects.create(question=self.question, option_text="Yes")

    def test_recipients_unique_and_send_skips_existing(self):
        self.assertEqual(send_survey(self.admin, self.survey, [self.customer.pk]), {"created": 1, "skipped": 0})
        self.assertEqual(send_survey(self.admin, self.survey, [self.customer.pk, self.customer.pk]), {"created": 0, "skipped": 1})
        self.client.force_login(self.admin)
        response = self.client.post(reverse("surveys:send", args=[self.survey.pk]), {"customer_id": [self.customer.pk]})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SurveyRecipient.objects.count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            SurveyRecipient.objects.create(survey=self.survey, customer=self.customer, status="SENT")

    def test_response_unique_and_double_submit_keeps_one_answer(self):
        recipient = SurveyRecipient.objects.create(survey=self.survey, customer=self.customer, status="SENT")
        answers = [{"question_id": self.question.pk, "option_id": self.option.pk}]
        self.assertTrue(submit_survey(self.account, recipient.pk, answers))
        self.assertFalse(submit_survey(self.account, recipient.pk, answers))
        self.assertEqual(SurveyAnswer.objects.count(), 1)
        self.assertEqual(SurveyResponse.objects.count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            SurveyResponse.objects.create(recipient=recipient, status="IN_PROGRESS")
        self.client.force_login(self.account)
        url = reverse("surveys:submit", args=[recipient.pk])
        self.assertEqual(self.client.post(url, {"answers": json.dumps(answers)}).status_code, 302)
        self.assertEqual(self.client.post(url, {"answers": json.dumps(answers)}).status_code, 302)
        self.assertEqual(SurveyAnswer.objects.count(), 1)
        self.assertRedirects(self.client.get(reverse("surveys:take", args=[recipient.pk])), reverse("surveys:result", args=[recipient.pk]))

    def test_answer_option_must_belong_to_question(self):
        recipient = SurveyRecipient.objects.create(survey=self.survey, customer=self.customer, status="SENT")
        other_question = SurveyQuestion.objects.create(survey=self.survey, question_text="Other", question_type="SINGLE_CHOICE")
        other_option = SurveyOption.objects.create(question=other_question, option_text="No")
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            submit_survey(self.account, recipient.pk, [{"question_id": self.question.pk, "option_id": other_option.pk}])
        self.assertEqual(SurveyAnswer.objects.count(), 0)

    def test_wrong_customer_cannot_take_or_submit(self):
        recipient = SurveyRecipient.objects.create(survey=self.survey, customer=self.customer, status="SENT")
        other = get_user_model().objects.create_user("other@example.com", "StrongPass!2026")
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("surveys:take", args=[recipient.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("surveys:submit", args=[recipient.pk]), {"answers": "[]"}).status_code, 403)
