"""Regressions for Account/Customer integration through real HTTP entry points."""
import json
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.services import create_account, delete_account
from apps.customers.forms import CustomerCreateForm
from apps.customers.models import Customer, CustomerPreference
from apps.customers.services import create_customer


class CustomerAccountLifecycleTests(TestCase):
    password = "Lifecycle!2026Secure"

    @classmethod
    def setUpTestData(cls):
        cls.admin = Account.objects.create_superuser("admin@lifecycle.test", cls.password)
        cls.manager = Account.objects.create_user("manager@lifecycle.test", cls.password)
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        cls.staff = Account.objects.create_user("staff@lifecycle.test", cls.password)
        cls.staff.groups.add(Group.objects.create(name="CUSTOMER_SERVICE"))

    def customer_payload(self, **extra):
        return {"email": "new@lifecycle.test", "full_name": "New Customer", "phone": "0901234567",
                "password": self.password, **extra}

    def account_payload(self, **extra):
        return {"email": "admin-created@lifecycle.test", "role": "customer", "status": "active",
                "password": self.password, "password_confirm": self.password, **extra}

    def assert_login_and_own_profile(self, account):
        client = Client()
        response = client.post(reverse("customer_auth:login"), {"email": account.email, "password": self.password})
        self.assertEqual(response.status_code, 302)
        response = client.get(reverse("customers:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["customer"].account_id, account.pk)
        return client

    def test_manager_create_login_profile_then_admin_delete_from_accounts(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("customers:create"), self.customer_payload(), follow=True)
        self.assertRedirects(response, reverse("customers:list"))
        self.assertNotContains(response, self.password)
        account = Account.objects.get(email="new@lifecycle.test")
        customer = Customer.objects.get(pk=account.pk)
        session = self.assert_login_and_own_profile(account)
        pref = CustomerPreference.objects.create(customer=customer, preference_type="BRAND", preference_value="Yonex")
        self.client.force_login(self.admin)
        response = self.client.post(reverse("accounts_admin:delete", args=[account.pk]), follow=True)
        self.assertContains(response, "Account deleted")
        self.assertFalse(Account.objects.filter(pk=account.pk).exists())
        self.assertFalse(Customer.objects.filter(pk=account.pk).exists())
        self.assertFalse(CustomerPreference.objects.filter(pk=pref.pk).exists())
        self.assertFalse(Client().login(email=account.email, password=self.password))
        self.assertNotEqual(session.get(reverse("customers:profile")).status_code, 200)
        # The old list is refetched after a redirect; no cached row remains.
        self.client.force_login(self.manager)
        self.assertNotContains(self.client.get(reverse("customers:list")), account.email)

    def test_admin_html_and_api_create_both_appear_for_manager_and_have_profile(self):
        for mode in ("html", "api"):
            with self.subTest(mode=mode):
                self.client.force_login(self.admin)
                data = self.account_payload(email=f"{mode}@lifecycle.test")
                if mode == "html":
                    response = self.client.post(reverse("accounts_admin:create"), data)
                    self.assertEqual(response.status_code, 302)
                else:
                    response = self.client.post("/api/accounts/", json.dumps(data), content_type="application/json")
                    self.assertEqual(response.status_code, 201, response.content)
                    self.assertNotIn("password", response.json())
                    self.assertNotIn("password_hash", response.json())
                self.assertNotContains(response, self.password, status_code=response.status_code)
                account = Account.objects.get(email=data["email"])
                self.assertEqual(Customer.objects.filter(pk=account.pk).count(), 1)
                self.client.force_login(self.manager)
                self.assertContains(self.client.get(reverse("customers:list")), account.email)
                self.assert_login_and_own_profile(account)

    def test_form_contract_password_errors_and_removed_fields_ignored(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("customers:create"))
        for field in ("play_styles", "brands"):
            self.assertNotContains(response, f'name="{field}"')
            self.assertNotIn(field, CustomerCreateForm().fields)
        self.assertContains(response, 'type="password"')
        self.assertContains(response, 'autocomplete="new-password"')
        self.assertContains(response, "customer-password-toggle")
        for password in ("", "123", "password", "12345678901", "new@lifecycle.test"):
            response = self.client.post(reverse("customers:create"), self.customer_payload(password=password))
            self.assertEqual(response.status_code, 200)
            self.assertIn("password", response.context["form"].errors)
            self.assertFalse(Account.objects.filter(email="new@lifecycle.test").exists())
        response = self.client.post(reverse("customers:create"), self.customer_payload(
            play_styles=["Forged style"], brands=["Forged brand"], role="ADMIN", status="LOCKED"))
        self.assertEqual(response.status_code, 302)
        customer = Customer.objects.get(email="new@lifecycle.test")
        self.assertEqual(customer.role, "CUSTOMER")
        self.assertEqual(customer.status, "ACTIVE")
        self.assertFalse(customer.customerpreference_set.exists())
        response = self.client.post(reverse("customers:create"), self.customer_payload())
        self.assertContains(response, "Email is already in use")
        self.assertContains(response, "Phone number is already in use")
        self.assertNotContains(response, self.password)

    def test_service_password_validation_and_profile_failure_roll_back_account(self):
        with self.assertRaises(ValidationError):
            create_customer(**self.customer_payload(password="123"))
        self.assertFalse(Account.objects.filter(email="new@lifecycle.test").exists())
        with patch("apps.customers.services.CustomerPreference.objects.bulk_create", side_effect=IntegrityError("profile failure")):
            with self.assertRaises(IntegrityError):
                create_customer(**self.customer_payload(play_styles=["ATTACK"]))
        self.assertFalse(Account.objects.filter(email="new@lifecycle.test").exists())
        with self.assertRaises(ValidationError):
            create_account(self.admin, email="rollback@lifecycle.test", role="CUSTOMER", status="ACTIVE", password="123")
        self.assertFalse(Account.objects.filter(email="rollback@lifecycle.test").exists())

    def test_own_profile_ignores_foreign_ids_and_customer_cannot_manage_accounts(self):
        first = create_customer(**self.customer_payload())
        other = create_customer(**self.customer_payload(email="other@lifecycle.test", phone="0907654321"))
        self.client.force_login(first.account)
        response = self.client.get(reverse("customers:profile"), {"customer_id": other.pk, "account_id": other.account_id})
        self.assertEqual(response.context["customer"].pk, first.pk)
        response = self.client.post(reverse("customers:profile"), {"full_name": "Own update", "phone": first.phone,
            "customer_id": other.pk, "account_id": other.account_id, "role": "ADMIN"})
        self.assertEqual(response.status_code, 302)
        other.refresh_from_db()
        first.refresh_from_db()
        self.assertEqual(first.full_name, "Own update")
        self.assertEqual(other.full_name, "New Customer")
        self.assertEqual(first.account.role, "CUSTOMER")
        for actor in (first.account, self.manager, self.staff):
            self.client.force_login(actor)
            response = self.client.delete(f"/api/accounts/{other.account_id}")
            self.assertEqual(response.status_code, 403)
        self.assertEqual(Customer.objects.get(pk=other.pk).status, "ACTIVE")

    def test_creation_and_deletion_still_require_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manager)
        self.assertEqual(client.post(reverse("customers:create"), self.customer_payload()).status_code, 403)
        token = client.get(reverse("customers:create")).cookies["csrftoken"].value
        self.assertEqual(client.post(reverse("customers:create"), self.customer_payload(), HTTP_X_CSRFTOKEN=token).status_code, 302)
        customer = Customer.objects.get(email="new@lifecycle.test")
        client.force_login(self.admin)
        self.assertEqual(client.post(reverse("accounts_admin:delete", args=[customer.account_id])).status_code, 403)


class RepairCustomerProfilesTests(TestCase):
    password = "Repair!2026Secure"

    def test_preview_apply_repeat_preserves_existing_profiles_staff_and_credentials(self):
        missing = Account.objects.create_user("missing@repair.test", self.password, full_name="")
        locked = Account.objects.create_user("locked@repair.test", self.password, status="LOCKED", full_name="")
        manager = Account.objects.create_user("manager@repair.test", self.password, role="MANAGER", full_name="Manager")
        staff = Account.objects.create_user("staff@repair.test", self.password, role="MANAGER", full_name="Staff")
        admin = Account.objects.create_superuser("admin@repair.test", self.password, full_name="Admin")
        existing = Account.objects.create_user("existing@repair.test", self.password, full_name="Existing")
        pref = CustomerPreference.objects.create(customer=existing, preference_type="PLAY_STYLE", preference_value="Saved")
        original_hashes = dict(Account.objects.values_list("pk", "password"))
        out = StringIO()
        call_command("repair_customer_profiles", stdout=out)
        self.assertIn("Missing profiles: 2", out.getvalue())
        call_command("repair_customer_profiles", apply=True, account_id=[missing.pk], stdout=StringIO())
        missing.refresh_from_db()
        self.assertEqual(missing.full_name, "missing@repair.test")
        call_command("repair_customer_profiles", apply=True, stdout=StringIO())
        call_command("repair_customer_profiles", apply=True, stdout=StringIO())
        locked.refresh_from_db()
        existing.refresh_from_db()
        self.assertEqual(locked.full_name, "locked@repair.test")
        self.assertEqual(existing.full_name, "Existing")
        self.assertTrue(CustomerPreference.objects.filter(pk=pref.pk).exists())
        self.assertEqual(dict(Account.objects.values_list("pk", "password")), original_hashes)
