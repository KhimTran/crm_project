"""Report/statistics empty, malformed identifier and date-boundary regressions."""
from datetime import timedelta
from unittest.mock import patch
from django.utils import timezone
from apps.accounts.models import Account
from apps.accounts.testing import PortalTestCase
from .models import Survey, SurveyQuestion, SurveyRecipient
from .services import start_survey
from django.core.exceptions import ValidationError


class SurveyAuditEdgesTests(PortalTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user('audit-edge-manager@test.example', 'AuditEdges!2026', role='MANAGER')
        cls.customer = Account.objects.create_user('audit-edge-customer@test.example', 'AuditEdges!2026')
        cls.other = Account.objects.create_user('audit-edge-other@test.example', 'AuditEdges!2026')
        cls.start = timezone.now().replace(microsecond=0)
        cls.survey = Survey.objects.create(title='Empty edge statistics', created_by=cls.manager,
            status='ACTIVE', start_at=cls.start, end_at=cls.start+timedelta(days=1))
        cls.question = SurveyQuestion.objects.create(survey=cls.survey, question_type='TEXT', question_text='Comment')

    def test_empty_reports_and_stats_render_without_inventing_responses(self):
        self.client.force_login(self.manager)
        customer_report = self.client.get('/crm/reports/customers/')
        self.assertEqual(customer_report.status_code, 200)
        results = self.client.get('/surveys/manage/results/')
        self.assertEqual(results.status_code, 200)
        self.assertEqual(results.context['report']['total']['count'], 0)
        self.assertIsNone(results.context['report']['csat']['avg'])
        self.assertIsNone(results.context['report']['nps']['score'])
        stats = self.client.get(f'/surveys/manage/{self.survey.pk}/stats/')
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.context['stats']['responses'], 0)
        self.assertIsNone(stats.context['stats']['rate'])

    def test_invalid_report_and_stats_identifiers_are_safe(self):
        self.client.force_login(self.manager)
        for identifier in ('not-a-number', '99999999999999999999999999999', '-1'):
            with self.subTest(identifier=identifier):
                result = self.client.get('/surveys/manage/results/', {'survey_id': identifier})
                self.assertEqual(result.status_code, 200)
                self.assertIsNone(result.context['report'])
                self.assertTrue(result.context['survey_error'])
        self.assertEqual(self.client.get('/surveys/manage/999999999/stats/').status_code, 404)

    def test_customer_cannot_read_manager_reports_or_foreign_recipient(self):
        recipient = SurveyRecipient.objects.create(survey=self.survey, customer=self.other, status='SENT')
        self.client.force_login(self.customer)
        for path in ('/crm/reports/customers/', '/surveys/manage/results/',
                     f'/surveys/manage/{self.survey.pk}/stats/'):
            with self.subTest(path=path):
                self.assertRedirects(self.client.get(path), '/', fetch_redirect_response=False)
        self.assertEqual(self.client.get(f'/surveys/recipients/{recipient.pk}/').status_code, 403)

    def test_schedule_start_and_end_are_inclusive_with_outside_instants_rejected(self):
        recipient = SurveyRecipient.objects.create(survey=self.survey, customer=self.customer, status='SENT')
        for instant in (self.start, self.survey.end_at):
            with self.subTest(instant=instant), patch('apps.surveys.services.timezone.now', return_value=instant):
                response, editable = start_survey(self.customer, recipient.pk)
                self.assertEqual(response.recipient_id, recipient.pk)
                self.assertTrue(editable)
        for instant in (self.start-timedelta(seconds=1), self.survey.end_at+timedelta(seconds=1)):
            with self.subTest(instant=instant), patch('apps.surveys.services.timezone.now', return_value=instant):
                with self.assertRaises(ValidationError):
                    start_survey(self.customer, recipient.pk)
