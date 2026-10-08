from django.test import TestCase

from apps.accounts.models import Account
from .models import Customer, CustomerPreference


class OwnProfileViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = Account.objects.create_user("owner@profile.test", "StrongPass!2026")
        cls.other = Account.objects.create_user("other@profile.test", "StrongPass!2026")
        cls.customer = Customer.objects.create(account=cls.owner, full_name="Owner")
        cls.other_customer = Customer.objects.create(account=cls.other, full_name="Other")
        cls.preference = CustomerPreference.objects.create(customer=cls.customer, preference_type="CATEGORY", preference_value="Badminton rackets")
        cls.other_preference = CustomerPreference.objects.create(customer=cls.other_customer, preference_type="CATEGORY", preference_value="Other rackets")

    def setUp(self):
        self.client.force_login(self.owner)

    def payload(self, **extra):
        return {"full_name": "Updated owner", "phone": "0912345678", "date_of_birth": "2000-01-01",
                "preferences-TOTAL_FORMS": "2", "preferences-INITIAL_FORMS": "1",
                "preferences-0-preference_id": str(self.preference.pk),
                "preferences-0-preference_type": "CATEGORY", "preferences-0-preference_value": "Updated rackets", **extra}

    def test_profile_page_is_owned_and_email_is_read_only(self):
        response = self.client.get("/account/profile/?customer_id=" + str(self.other_customer.pk))
        self.assertContains(response, self.owner.email)
        self.assertContains(response, "Badminton rackets")
        self.assertNotContains(response, "Other rackets")
        self.assertNotContains(response, 'name="email"')
        self.assertNotContains(response, 'name="account_id"')

    def test_edit_profile_update_add_delete_preferences_and_ignore_privilege_fields(self):
        data = self.payload(email=self.other.email, account_id=self.other.pk, customer_id=self.other_customer.pk,
                            role="ADMIN", status="DELETED", groups="CRM_MANAGER", permissions="*",
                            **{"preferences-1-preference_type": "CATEGORY", "preferences-1-preference_value": "New category"})
        self.assertRedirects(self.client.post("/account/profile/", data), "/account/profile/", fetch_redirect_response=False)
        self.customer.refresh_from_db()
        self.owner.refresh_from_db()
        self.other_customer.refresh_from_db()
        self.assertEqual((self.customer.full_name, self.customer.status, self.customer.account_id), ("Updated owner", "ACTIVE", self.owner.pk))
        self.assertEqual((self.owner.email, self.owner.role, self.owner.status), ("owner@profile.test", "CUSTOMER", "ACTIVE"))
        self.assertFalse(self.owner.groups.exists())
        self.assertEqual(self.other_customer.full_name, "Other")
        self.assertEqual(CustomerPreference.objects.filter(customer=self.customer).count(), 2)
        self.assertRedirects(self.client.post("/account/profile/", self.payload(**{"preferences-0-DELETE": "on"})), "/account/profile/", fetch_redirect_response=False)
        self.assertFalse(CustomerPreference.objects.filter(pk=self.preference.pk).exists())

    def test_forged_preference_id_does_not_modify_or_delete_other_preferences(self):
        for delete in ("", "on"):
            response = self.client.post("/account/profile/", self.payload(**{
                "preferences-0-preference_id": str(self.other_preference.pk), "preferences-0-DELETE": delete,
            }))
            self.assertIn(response.status_code, (200, 403))
            self.other_preference.refresh_from_db()
            self.assertEqual(self.other_preference.preference_value, "Other rackets")
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.full_name, "Owner")

    def test_invalid_phone_date_or_preference_does_not_partially_save(self):
        for data in (self.payload(phone="bad"), self.payload(date_of_birth="9999-01-01"),
                     self.payload(**{"preferences-0-preference_value": "x" * 151}),
                     {"full_name": "Changed without formset"}):
            response = self.client.post("/account/profile/", data)
            self.assertEqual(response.status_code, 200)
            self.customer.refresh_from_db()
            self.assertEqual(self.customer.full_name, "Owner")
            self.preference.refresh_from_db()
            self.assertEqual(self.preference.preference_value, "Badminton rackets")

    def test_missing_or_deleted_customer_is_not_created_implicitly(self):
        no_profile = Account.objects.create_user("missing@profile.test", "StrongPass!2026")
        self.client.force_login(no_profile)
        self.assertEqual(self.client.get("/account/profile/").status_code, 403)
        Customer.objects.filter(pk=self.customer.pk).update(status="DELETED")
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get("/account/profile/").status_code, 403)
