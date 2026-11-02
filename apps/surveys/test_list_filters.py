from apps.accounts.testing import PortalTestCase as TestCase
from datetime import datetime

from django.core.paginator import Paginator

from django.utils import timezone

from apps.accounts.models import Account
from .forms import SurveyListFilterForm
from .models import Survey
from .selectors import survey_list_queryset


class SurveyListFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user('manager@list.test', 'StrongPass!2026', role='MANAGER')
        def at(day, hour=0):
            return timezone.make_aware(datetime(2030, 6, day, hour))
        for pk, title, status, start, end in [
            (30, 'Vợt tháng sáu', 'ACTIVE', at(15), at(25)),
            (5, 'Vợt đầu tháng', 'DRAFT', at(1), at(10)),
            (12, 'Giày giữa tháng', 'CLOSED', at(10), at(20)),
            (50, 'Vợt chưa lên lịch', 'DRAFT', None, None),
            (70, 'Vợt thiếu ngày kết thúc', 'DRAFT', at(10), None),
            (80, 'Vợt cuối ngày', 'DRAFT', at(10, 23), at(11)),
        ]:
            Survey.objects.create(survey_id=pk, title=title, status=status, start_at=start, end_at=end, created_by=cls.manager)

    def ids(self, **params):
        form = SurveyListFilterForm(params)
        self.assertTrue(form.is_valid(), form.errors)
        return list(survey_list_queryset(form.cleaned_data).values_list('pk', flat=True))

    def test_default_search_status_and_clear(self):
        self.assertEqual(self.ids(), [5, 12, 30, 50, 70, 80])
        self.assertEqual(self.ids(q='Giày'), [12])
        self.assertEqual(self.ids(status='ACTIVE'), [30])
        self.assertEqual(self.ids(q='Vợt', status='DRAFT'), [5, 50, 70, 80])

    def test_one_sided_ranges_and_missing_schedule(self):
        self.assertEqual(self.ids(date_from='2030-06-20'), [12, 30])
        self.assertEqual(self.ids(date_to='2030-06-10'), [5, 12, 80])
        self.assertEqual(self.ids(date_from='2030-06-26'), [])

    def test_overlap_inclusive_boundaries_and_combination(self):
        self.assertEqual(self.ids(date_from='2030-06-10', date_to='2030-06-10'), [5, 12, 80])
        self.assertEqual(self.ids(date_from='2030-06-9', date_to='2030-06-16'), [5, 12, 30, 80])
        self.assertEqual(self.ids(q='Vợt', status='ACTIVE', date_from='2030-06-20', date_to='2030-06-22'), [30])
        pages = Paginator(survey_list_queryset({}), 2)
        self.assertEqual([row.pk for page in pages for row in page], [5, 12, 30, 50, 70, 80])

    def test_invalid_dates_and_status(self):
        for params in [{'date_from': '2030-06-20', 'date_to': '2030-06-10'}, {'date_from': 'bad'}, {'date_to': '2030-02-30'}, {'status': 'INVALID'}]:
            self.assertFalse(SurveyListFilterForm(params).is_valid())

    def test_existing_survey_pages_and_access_guard(self):
        self.assertNotEqual(self.client.get('/surveys/manage/').status_code, 200)
        self.client.post('/manager/login/', {'email': self.manager.email, 'password': 'StrongPass!2026'})
        for url in ['/surveys/manage/new/', '/surveys/manage/5/', '/surveys/manage/5/edit/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get('/surveys/manage/5/delete/').status_code, 405)

    def test_manager_filter_state_errors_and_existing_actions(self):
        self.client.post('/manager/login/', {'email': self.manager.email, 'password': 'StrongPass!2026'})
        response = self.client.get('/surveys/manage/', {'q': 'Vợt', 'status': 'DRAFT', 'date_from': '2030-06-10', 'date_to': '2030-06-10'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([row.pk for row in response.context['items']], [5, 80])
        self.assertContains(response, 'value="2030-06-10"')
        self.assertContains(response, 'value="DRAFT" selected')
        for url in ['/surveys/manage/new/', '/surveys/manage/5/', '/surveys/manage/5/edit/', '/surveys/manage/5/delete/']:
            self.assertContains(response, url)
        invalid = self.client.get('/surveys/manage/', {'date_from': '2030-06-20', 'date_to': '2030-06-10'})
        self.assertContains(invalid, 'From Date must be on or before To Date.')
        self.assertEqual(invalid.context['items'], [])
        cleared = self.client.get('/surveys/manage/')
        self.assertEqual([row.pk for row in cleared.context['items']], [5, 12, 30, 50, 70, 80])
