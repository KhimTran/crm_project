from datetime import date, timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.urls import reverse

from apps.accounts.birth_dates import BirthDateField, latest_birth_date, validate_birth_date
from apps.accounts.forms import AccountCreateForm, AccountProfileEditForm, PersonalProfileEditForm
from apps.accounts.models import Account
from apps.accounts.services import update_account_profile
from apps.accounts.testing import PortalTestCase
from apps.customers.forms import CustomerCreateForm, CustomerEditForm
from apps.customers.self_service_forms import CustomerProfileForm
from apps.customers.services import create_customer

TODAY = date(2026, 11, 3)
PW = "StrongPass!2026"


class BirthDateBoundaryTests(SimpleTestCase):
    @patch("apps.accounts.birth_dates.timezone.localdate", return_value=TODAY)
    def test_exact_birthday_and_one_day_underage(self, _today):
        for age in (14, 18):
            with self.subTest(age=age):
                cutoff = latest_birth_date(age)
                validate_birth_date(cutoff, age)
                validate_birth_date(cutoff - timedelta(days=1), age)
                with self.assertRaisesMessage(ValidationError, f"at least {age}"):
                    validate_birth_date(cutoff + timedelta(days=1), age)
                with self.assertRaisesMessage(ValidationError, "future"):
                    validate_birth_date(TODAY + timedelta(days=1), age)

    def test_leap_day_uses_completed_calendar_years(self):
        self.assertEqual(latest_birth_date(18, date(2024, 2, 29)), date(2006, 2, 28))
        with patch("apps.accounts.birth_dates.timezone.localdate", return_value=date(2026, 2, 28)):
            with self.assertRaises(ValidationError):
                validate_birth_date(date(2012, 2, 29), 14)
        with patch("apps.accounts.birth_dates.timezone.localdate", return_value=date(2026, 3, 1)):
            validate_birth_date(date(2012, 2, 29), 14)

    @patch("apps.accounts.birth_dates.timezone.localdate", return_value=TODAY)
    def test_optional_invalid_and_calendar_bounds(self, _today):
        for age in (14, 18):
            field = BirthDateField(minimum_age=age, required=False)
            self.assertIsNone(field.clean(""))
            with self.assertRaises(ValidationError):
                field.clean("not-a-date")
            with self.assertRaises(ValidationError):
                field.clean("2026-02-30")
            html = field.widget.render("date_of_birth", None)
            self.assertIn(f'max="{latest_birth_date(age)}"', html)


class BirthDateFlowTests(PortalTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Account.objects.create_superuser("admin@birth.test", PW, full_name="Admin")
        cls.manager = Account.objects.create_user("manager@birth.test", PW, role="MANAGER", full_name="Manager")
        cls.customer = Account.objects.create_user("customer@birth.test", PW, full_name="Customer")

    def setUp(self):
        clock = patch("apps.accounts.birth_dates.timezone.localdate", return_value=TODAY)
        clock.start()
        self.addCleanup(clock.stop)

    def test_create_form_uses_target_role_and_normalizes_role(self):
        for role, age in [(" admin ", 18), ("manager", 18), ("customer", 14)]:
            for days, valid in [(0, True), (1, False)]:
                form = AccountCreateForm({"email": "new@birth.test", "role": role, "status": "ACTIVE",
                                          "password": PW, "password_confirm": PW,
                                          "date_of_birth": latest_birth_date(age) + timedelta(days=days)})
                self.assertEqual(form.is_valid(), valid, form.errors)
                if not valid:
                    self.assertIn("date_of_birth", form.errors)
                self.assertIn(f'max="{latest_birth_date(age)}"', str(form["date_of_birth"]))

    def test_staff_personal_profiles_reject_underage_and_future_without_writes(self):
        for actor, path in [(self.admin, "/admin/profile/"), (self.manager, "/manager/profile/")]:
            self.client.force_login(actor)
            self.assertContains(self.client.get(path), 'max="2008-11-03"')
            for dob in ("2008-11-04", "2026-11-04"):
                response = self.client.post(path, {"save_profile": "1", "full_name": "Changed", "date_of_birth": dob})
                self.assertEqual(response.status_code, 200)
                self.assertIn("date_of_birth", response.context["profile_form"].errors)
                actor.refresh_from_db()
                self.assertIsNone(actor.date_of_birth)
            self.assertEqual(self.client.post(path, {"save_profile": "1", "full_name": actor.full_name,
                                                    "date_of_birth": "2008-11-03"}).status_code, 302)

    def test_admin_edit_uses_target_account_role_not_posted_role(self):
        self.client.force_login(self.admin)
        for actor, age in [(self.manager, 18), (self.customer, 14)]:
            form = AccountProfileEditForm(account_id=actor.pk)
            self.assertIn(f'max="{latest_birth_date(age)}"', str(form["date_of_birth"]))
            response = self.client.post(reverse("accounts_admin:profile_update", args=[actor.pk]), {
                "full_name": "Unchanged", "date_of_birth": latest_birth_date(age) + timedelta(days=1),
                "role": "CUSTOMER"}, follow=True)
            self.assertEqual(response.status_code, 200)
            actor.refresh_from_db()
            self.assertIsNone(actor.date_of_birth)

    def test_customer_forms_registration_and_own_profile_require_fourteen(self):
        for form in (CustomerCreateForm(), CustomerEditForm(), CustomerProfileForm()):
            with self.subTest(form=type(form).__name__):
                self.assertIn('max="2012-11-03"', str(form["date_of_birth"]))
                with self.assertRaises(ValidationError):
                    form.fields["date_of_birth"].clean("2012-11-04")
                self.assertEqual(form.fields["date_of_birth"].clean("2012-11-03"), date(2012, 11, 3))
        payload = {"full_name": "New Customer", "email": "register@birth.test", "password": PW,
                   "password_confirm": PW, "date_of_birth": "2012-11-04"}
        response = self.client.post("/register/", payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Account.objects.filter(email=payload["email"]).exists())
        payload["date_of_birth"] = "2012-11-03"
        self.assertEqual(self.client.post("/register/", payload).status_code, 302)
        self.client.force_login(self.customer)
        response = self.client.post("/account/profile/", {"full_name": "Customer", "date_of_birth": "2012-11-04"})
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertIsNone(self.customer.date_of_birth)

    def test_model_and_services_cannot_bypass_age_validation(self):
        with self.assertRaises(ValidationError):
            update_account_profile(self.admin, self.manager.pk, {"date_of_birth": date(2008, 11, 4)})
        with self.assertRaises(ValidationError):
            create_customer(email="young@birth.test", password=PW, full_name="Too young", phone="0901234567",
                            date_of_birth=date(2012, 11, 4))
        self.assertFalse(Account.objects.filter(email="young@birth.test").exists())
        self.manager.refresh_from_db()
        self.assertIsNone(self.manager.date_of_birth)

    def test_historical_birth_dates_do_not_block_lock_or_password_operations(self):
        Account.objects.filter(pk=self.customer.pk).update(date_of_birth=date(2020, 1, 1))
        self.customer.refresh_from_db()
        self.customer.status = "LOCKED"
        self.customer.save(update_fields=["status"])
        self.customer.set_password("AnotherStrong!2026")
        self.customer.save(update_fields=["password"])
        self.customer.date_of_birth = date(2021, 1, 1)
        with self.assertRaises(ValidationError):
            self.customer.save()

    def test_underage_customer_cannot_be_promoted_to_manager(self):
        self.customer.date_of_birth = date(2010, 1, 1)
        self.customer.save()
        self.client.force_login(self.admin)
        response = self.client.post(reverse("accounts_admin:role", args=[self.customer.pk]), {"role": "MANAGER"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, "CUSTOMER")
