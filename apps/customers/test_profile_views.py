from unittest.mock import patch

from django.test import TestCase

from apps.accounts.models import Account
from apps.catalog.models import Category
from .models import Customer, CustomerPreference
from .self_services import update_own_profile


class OwnProfileViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = Account.objects.create_user('owner@profile.test', 'StrongPass!2026')
        cls.other = Account.objects.create_user('other@profile.test', 'StrongPass!2026')
        cls.customer = Customer.objects.create(account=cls.owner, full_name='Owner', gender='Old gender', playing_level='ADVANCED')
        cls.other_customer = Customer.objects.create(account=cls.other, full_name='Other')
        cls.category = Category.objects.create(category_name='Badminton rackets')
        cls.second = Category.objects.create(category_name='Shoes')
        cls.inactive = Category.objects.create(category_name='Old category', status='INACTIVE')
        cls.preference = CustomerPreference.objects.create(customer=cls.customer, preference_type='CATEGORY', preference_value='Badminton rackets')
        cls.legacy = CustomerPreference.objects.create(customer=cls.customer, preference_type='CATEGORY', preference_value='Old category')
        cls.brand = CustomerPreference.objects.create(customer=cls.customer, preference_type='BRAND', preference_value='Yonex')
        cls.other_preference = CustomerPreference.objects.create(customer=cls.other_customer, preference_type='CATEGORY', preference_value='Other rackets')

    def setUp(self):
        self.client.force_login(self.owner)

    def payload(self, **extra):
        return {'full_name': 'Updated owner', 'phone': '0912345678', 'date_of_birth': '2000-01-01',
                'gender': 'Old gender', 'playing_level': 'ADVANCED', 'categories': [self.category.pk], **extra}

    def test_profile_page_owned_preselects_names_and_uses_customer_labels(self):
        response = self.client.get('/account/profile/?customer_id=' + str(self.other_customer.pk))
        self.assertContains(response, self.owner.email)
        self.assertContains(response, 'Badminton rackets')
        self.assertNotContains(response, 'Other rackets')
        for forbidden in ('name="email"', 'name="account_id"', 'CATEGORY', 'preference_type', 'Loại sở thích'):
            self.assertNotContains(response, forbidden)
        self.assertContains(response, 'Danh mục bạn quan tâm')
        self.assertContains(response, 'Sở thích đã lưu khác')
        self.assertEqual(response.context['preferences'].initial['categories'], [self.category.pk])
        self.assertContains(response, f'value="{self.category.pk}" id="id_categories_0" checked')
        self.assertContains(response, '<select name="gender"')
        self.assertContains(response, '<select name="playing_level"')
        self.assertContains(response, 'Đã lưu: Old gender')
        self.assertContains(response, 'Đã lưu: ADVANCED')

    def test_multiple_sync_remove_repeat_and_privilege_fields_ignored(self):
        data = self.payload(categories=[self.category.pk, self.second.pk], email=self.other.email,
                            account_id=self.other.pk, customer_id=self.other_customer.pk,
                            role='ADMIN', status='DELETED', groups='CRM_MANAGER', permissions='*',
                            preference_type='BRAND', preference_value='Forged')
        for _ in range(2):
            self.assertRedirects(self.client.post('/account/profile/', data), '/account/profile/', fetch_redirect_response=False)
        self.customer.refresh_from_db()
        self.owner.refresh_from_db()
        self.other_customer.refresh_from_db()
        self.assertEqual((self.customer.full_name, self.customer.status, self.customer.account_id), ('Updated owner', 'ACTIVE', self.owner.pk))
        self.assertEqual((self.owner.email, self.owner.role, self.owner.status), ('owner@profile.test', 'CUSTOMER', 'ACTIVE'))
        self.assertFalse(self.owner.groups.exists())
        self.assertEqual(self.other_customer.full_name, 'Other')
        self.assertEqual(self.customer.customerpreference_set.count(), 4)
        self.assertRedirects(self.client.post('/account/profile/', self.payload(categories=[self.second.pk])), '/account/profile/', fetch_redirect_response=False)
        self.assertFalse(CustomerPreference.objects.filter(pk=self.preference.pk).exists())
        self.assertTrue(CustomerPreference.objects.filter(pk=self.legacy.pk).exists())
        self.assertTrue(CustomerPreference.objects.filter(pk=self.brand.pk, preference_value='Yonex').exists())

    def test_removal_explicit_and_foreign_or_other_type_ids_cannot_be_deleted(self):
        for invalid in (self.other_preference.pk, self.brand.pk, self.preference.pk, 999999, 'bad'):
            with self.subTest(preference_id=invalid):
                response = self.client.post('/account/profile/', self.payload(remove_preferences=[invalid]))
                self.assertEqual(response.status_code, 200)
                self.assertIn('remove_preferences', response.context['preferences'].errors)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.full_name, 'Owner')
        self.assertRedirects(self.client.post('/account/profile/', self.payload(remove_preferences=[self.legacy.pk])), '/account/profile/', fetch_redirect_response=False)
        self.assertFalse(CustomerPreference.objects.filter(pk=self.legacy.pk).exists())
        self.assertTrue(CustomerPreference.objects.filter(pk=self.other_preference.pk).exists())
        self.assertTrue(CustomerPreference.objects.filter(pk=self.brand.pk).exists())

    def test_invalid_profile_or_category_does_not_partially_save(self):
        for data in (self.payload(phone='bad'), self.payload(date_of_birth='9999-01-01'),
                     self.payload(categories=[999999]), self.payload(categories=[self.inactive.pk]),
                     self.payload(gender='UNKNOWN'), self.payload(playing_level='INTERMEDIATE')):
            response = self.client.post('/account/profile/', data)
            self.assertEqual(response.status_code, 200)
            self.customer.refresh_from_db()
            self.preference.refresh_from_db()
            self.assertEqual(self.customer.full_name, 'Owner')
            self.assertEqual(self.preference.preference_value, 'Badminton rackets')

    def test_category_disabled_between_form_validation_and_service_is_form_error(self):
        def disable_then_save(*args, **kwargs):
            Category.objects.filter(pk=self.category.pk).update(status='INACTIVE')
            return update_own_profile(*args, **kwargs)
        with patch('apps.customers.views.update_own_profile', side_effect=disable_then_save):
            response = self.client.post('/account/profile/', self.payload())
        self.assertEqual(response.status_code, 200)
        self.assertIn('categories', response.context['preferences'].errors)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.full_name, 'Owner')
        self.assertTrue(CustomerPreference.objects.filter(pk=self.preference.pk).exists())

    def test_no_active_categories_preserves_saved_data_and_displays_empty_state(self):
        Category.objects.update(status='INACTIVE')
        response = self.client.get('/account/profile/')
        self.assertContains(response, 'Hiện chưa có danh mục để chọn')
        self.assertContains(response, 'Badminton rackets')
        self.assertRedirects(self.client.post('/account/profile/', self.payload(categories=[])), '/account/profile/', fetch_redirect_response=False)
        self.assertEqual(self.customer.customerpreference_set.count(), 3)

    def test_legacy_dropdown_values_preserved_then_change_to_tv4_values(self):
        self.assertRedirects(self.client.post('/account/profile/', self.payload()), '/account/profile/', fetch_redirect_response=False)
        self.customer.refresh_from_db()
        self.assertEqual((self.customer.gender, self.customer.playing_level), ('Old gender', 'ADVANCED'))
        self.assertRedirects(self.client.post('/account/profile/', self.payload(gender='FEMALE', playing_level='RECREATIONAL')), '/account/profile/', fetch_redirect_response=False)
        self.customer.refresh_from_db()
        self.assertEqual((self.customer.gender, self.customer.playing_level), ('FEMALE', 'RECREATIONAL'))

    def test_missing_or_deleted_customer_not_created_implicitly(self):
        no_profile = Account.objects.create_user('missing@profile.test', 'StrongPass!2026')
        self.client.force_login(no_profile)
        self.assertEqual(self.client.get('/account/profile/').status_code, 403)
        Customer.objects.filter(pk=self.customer.pk).update(status='DELETED')
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get('/account/profile/').status_code, 403)
