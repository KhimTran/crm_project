from apps.accounts.testing import PortalTestCase as TestCase
from datetime import timedelta
from django.core.exceptions import ValidationError

from django.utils import timezone
from django.db import IntegrityError, transaction, connection
from apps.accounts.models import Account
from apps.customers.models import CustomerPreference
from apps.customers.reports import preference_report
from .configuration import populate_questionnaire
from .forms import AudienceForm
from .models import Survey, SurveyRecipient
from .services import resolve_audience, preference_choices


class SavedAudienceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'StrongPass!2026'
        cls.manager = Account.objects.create_user('manager@saved.test', cls.password, role='MANAGER')
        cls.first = Account.objects.create_user('first@saved.test', cls.password, full_name='First customer', playing_level='BEGINNER')
        cls.second = Account.objects.create_user('second@saved.test', cls.password, full_name='Second customer', playing_level='COMPETITIVE')
        cls.locked = Account.objects.create_user('locked@saved.test', cls.password, status='LOCKED')
        CustomerPreference.objects.create(customer=cls.first, preference_type='BRAND', preference_value='Yonex')
        CustomerPreference.objects.create(customer=cls.first, preference_type='CATEGORY', preference_value='Rackets')

    def login(self):
        self.client.post('/manager/login/', {'email': self.manager.email, 'password': self.password})

    def survey(self, audience):
        survey = Survey.objects.create(title='Saved audience test', status='DRAFT', created_by=self.manager,
                                       start_at=timezone.now(), end_at=timezone.now()+timedelta(days=7), audience=audience)
        populate_questionnaire(survey)
        return survey

    def test_all_group_and_specific_send_without_recipient_payload(self):
        self.login()
        for audience, expected in [({'audience':'all'}, {self.first.pk,self.second.pk}),
                                   ({'audience':'filter','playing_levels':['BEGINNER']}, {self.first.pk}),
                                   ({'audience':'pick','customer_ids':[self.second.pk,self.locked.pk]}, {self.second.pk})]:
            survey=self.survey(audience)
            url=f'/surveys/manage/{survey.pk}/audience/'
            page=self.client.get(url)
            self.assertEqual(page.status_code,200)
            for name in ['audience','customer_ids','playing_levels','preferences']:
                self.assertNotContains(page, f'name="{name}"')
            result=self.client.post(url, {'action':'send','audience':'pick','customer_ids':[self.locked.pk]})
            self.assertEqual(result.status_code,302)
            self.assertEqual(set(SurveyRecipient.objects.filter(survey=survey).values_list('customer_id',flat=True)),expected)
            survey.refresh_from_db()
            self.assertEqual(survey.audience,audience)
            self.client.post(url,{'action':'send'})
            self.assertEqual(SurveyRecipient.objects.filter(survey=survey).count(),len(expected))

    def test_missing_audience_cannot_silently_send_to_everyone(self):
        self.login(); survey=self.survey({})
        page=self.client.post(f'/surveys/manage/{survey.pk}/audience/',{'action':'send','audience':'all'})
        self.assertContains(page,'Save a valid survey audience')
        self.assertFalse(SurveyRecipient.objects.filter(survey=survey).exists())
        with self.assertRaises(ValidationError): resolve_audience({'audience':'filter'})

    def test_customer_pages_hide_style_but_keep_brand_and_category(self):
        self.login()
        detail=self.client.get(f'/crm/customers/{self.first.pk}/')
        self.assertEqual(detail.status_code,200)
        self.assertNotContains(detail,'Play Style')
        self.assertNotContains(detail,'ATTACK_LEGACY')
        self.assertContains(detail,'Yonex'); self.assertContains(detail,'Rackets')
        self.client.post('/login/',{'email':self.first.email,'password':self.password})
        profile=self.client.get('/account/profile/')
        self.assertEqual(profile.status_code,200)
        self.assertNotContains(profile,'ATTACK_LEGACY')
        # BRAND rows are no longer listed on the customer profile (panel removed); the CRM detail above still shows them.
        self.assertNotContains(profile,'Lựa chọn khác đã lưu')
        self.assertTrue(CustomerPreference.objects.filter(customer=self.first, preference_type='BRAND', preference_value='Yonex').exists())

    def test_builder_label_and_saved_audience_edit(self):
        self.login(); survey=self.survey({'audience':'pick','customer_ids':[self.first.pk]})
        for url in ['/surveys/manage/new/',f'/surveys/manage/{survey.pk}/edit/']:
            page=self.client.get(url)
            self.assertEqual(page.status_code,200)
            self.assertContains(page,'Single choice')
            self.assertNotContains(page,'choice (pick 1)')

    def test_legacy_admin_send_route_also_uses_saved_rules(self):
        admin=Account.objects.create_superuser('admin@saved.test',self.password)
        self.client.post('/admin/login/',{'email':admin.email,'password':self.password})
        survey=self.survey({'audience':'pick','customer_ids':[self.first.pk]})
        response=self.client.post(f'/surveys/{survey.pk}/send/',{'customer_id':[self.second.pk]})
        self.assertEqual(response.status_code,302)
        self.assertEqual(list(SurveyRecipient.objects.filter(survey=survey).values_list('customer_id',flat=True)),[self.first.pk])

    def test_database_rejects_retired_style_type(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CustomerPreference.objects.create(customer=self.first, preference_type='PLAY_STYLE', preference_value='Blocked')
        self.assertTrue(CustomerPreference.objects.filter(customer=self.first, preference_type='BRAND').exists())
        self.assertTrue(CustomerPreference.objects.filter(customer=self.first, preference_type='CATEGORY').exists())

    def test_supported_preference_types_remain_writable(self):
        for kind in ('BRAND','CATEGORY','FAVORITE_BRAND','FAVORITE_BRAND_OTHER'):
            preference=CustomerPreference.objects.create(customer=self.first,preference_type=kind,preference_value='Audit supported value')
            preference.refresh_from_db()
            self.assertEqual(preference.preference_type,kind)

    def test_cleanup_refuses_to_broaden_a_saved_style_segment(self):
        from importlib import import_module
        from types import SimpleNamespace
        from django.apps import apps
        survey=self.survey({'audience':'filter','preferences':['Tấn công']})
        cleanup=import_module('apps.customers.migrations.0003_remove_play_style').remove_play_style
        with self.assertRaises(RuntimeError):
            cleanup(apps, SimpleNamespace(connection=connection))
        survey.refresh_from_db()
        self.assertEqual(survey.audience['preferences'], ['Tấn công'])
