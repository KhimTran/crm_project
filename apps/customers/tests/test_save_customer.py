"""Save Customer's JSON submission uses the real database and existing RBAC."""
from unittest.mock import patch

from django.db import DatabaseError, IntegrityError
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import Account
from apps.customers.errors import DuplicateCustomerEmail, DuplicateCustomerPhone
from apps.customers.models import Customer


class SaveCustomerTests(TestCase):
    password = "SaveFixture!2026Secure"

    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@save.test", cls.password, role="MANAGER")
        cls.admin = Account.objects.create_superuser("admin@save.test", cls.password)
        cls.shopper = Account.objects.create_user("shopper@save.test", cls.password)
        cls.url = reverse("customers:create")

    def setUp(self):
        self.client.force_login(self.manager)

    def payload(self, **changes):
        return {"full_name": "Saved Customer", "email": "saved@save.test", "phone": "0901234567",
                "password": self.password, **changes}

    def save(self, **changes):
        return self.client.post(self.url, self.payload(**changes), HTTP_ACCEPT="application/json")

    def test_save_persists_hash_profile_and_returns_fresh_list_without_password(self):
        response = self.save(role="ADMIN", status="LOCKED", play_styles="ignored", brands="ignored")
        self.assertEqual(response.status_code, 201)
        customer = Customer.objects.get(pk=response.json()["customer_id"])
        self.assertEqual((customer.account.role, customer.account.status), ("CUSTOMER", "ACTIVE"))
        self.assertTrue(customer.account.check_password(self.password))
        self.assertNotEqual(customer.account.password, self.password)
        self.assertFalse(customer.customerpreference_set.exists())
        self.assertNotContains(response, self.password, status_code=201)
        self.assertNotContains(response, customer.account.password, status_code=201)
        self.assertIn(customer.account.email, response.json()["html"])
        self.assertIn("customer-created-message", response.json()["html"])
        self.assertEqual(response.json()["list_url"], reverse("customers:list"))
        # A fresh HTTP request sees the committed row, not just client state.
        for actor in (self.admin, self.manager):
            self.client.force_login(actor)
            self.assertContains(self.client.get(reverse("customers:list")), customer.account.email)
        shopper = Client()
        self.assertTrue(shopper.login(email=customer.account.email, password=self.password))
        self.assertEqual(shopper.get(reverse("customers:profile")).context["customer"].pk, customer.pk)

    def test_missing_invalid_and_duplicate_data_return_field_errors(self):
        response = self.client.post(self.url, {}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()["errors"]), {"full_name", "email", "phone", "password"})
        response = self.save(email="bad", password="123", phone="123", date_of_birth="2999-01-01")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()["errors"]), {"email", "phone", "password", "date_of_birth"})
        self.assertFalse(Customer.objects.filter(email="saved@save.test").exists())
        self.assertEqual(self.save().status_code, 201)
        # Even if two HTTP requests get through, the same account is not created twice.
        duplicate = self.save()
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("already in use", duplicate.json()["errors"]["email"][0])
        self.assertIn("already in use", duplicate.json()["errors"]["phone"][0])
        self.assertEqual(Customer.objects.filter(email="saved@save.test").count(), 1)
        self.assertEqual(Account.objects.filter(email="saved@save.test").count(), 1)

    def test_service_duplicate_races_are_field_errors(self):
        for exception, field in ((DuplicateCustomerEmail("Email đã được sử dụng"), "email"),
                                 (DuplicateCustomerPhone("Số điện thoại đã được sử dụng"), "phone")):
            with self.subTest(field=field), patch("apps.customers.views.create_customer", side_effect=exception):
                response = self.save()
                self.assertEqual(response.status_code, 409)
                self.assertIn(field, response.json()["errors"])
        self.assertFalse(Customer.objects.filter(email="saved@save.test").exists())

    def test_database_failure_rolls_back_and_retry_succeeds(self):
        with patch("apps.customers.services.Account.objects.create_user", side_effect=IntegrityError("private DB details")):
            response = self.save()
        self.assertEqual(response.status_code, 503)
        self.assertIn("Unable to save", response.json()["errors"]["__all__"][0])
        self.assertNotContains(response, "private DB details", status_code=503)
        self.assertNotContains(response, self.password, status_code=503)
        self.assertFalse(Account.objects.filter(email="saved@save.test").exists())
        self.assertEqual(self.save().status_code, 201)

    def test_list_response_failure_also_rolls_back(self):
        with patch("apps.customers.views.render_to_string", side_effect=DatabaseError("list read failed")):
            response = self.save()
        self.assertEqual(response.status_code, 503)
        self.assertFalse(Account.objects.filter(email="saved@save.test").exists())
        self.assertFalse(Customer.objects.filter(email="saved@save.test").exists())

    def test_json_requires_existing_permissions_active_session_and_csrf(self):
        for actor in (None, self.shopper):
            self.client.logout()
            if actor:
                self.client.force_login(actor)
            self.assertNotEqual(self.save().status_code, 201)
        self.client.force_login(self.manager)
        Account.objects.filter(pk=self.manager.pk).update(status="LOCKED")
        self.assertNotEqual(self.save().status_code, 201)
        Account.objects.filter(pk=self.manager.pk).update(status="ACTIVE")
        self.assertFalse(Customer.objects.filter(email="saved@save.test").exists())
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.manager)
        self.assertEqual(csrf_client.post(self.url, self.payload(), HTTP_ACCEPT="application/json").status_code, 403)
        token = csrf_client.get(self.url).cookies["csrftoken"].value
        response = csrf_client.post(self.url, self.payload(), HTTP_ACCEPT="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 201)

    def test_create_uses_catalog_panel_and_keeps_html_fallback(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'portal-panel customer-create-page')
        self.assertContains(response, 'class="btn btn-primary"')
        self.assertContains(response, "Back to list")
        self.assertNotContains(response, 'name="play_styles"')
        self.assertNotContains(response, 'name="brands"')
        response = self.client.post(self.url, self.payload())
        self.assertRedirects(response, reverse("customers:list"))
