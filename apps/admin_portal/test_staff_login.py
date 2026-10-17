"""Staff-login denial must leave an existing customer session intact."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.constants import AccountRole


class StaffLoginCustomerSessionTests(TestCase):
    password = "StaffLoginPass!2026"
    login_paths = ("/admin/login/", "/manager/login/")

    @classmethod
    def setUpTestData(cls):
        account = get_user_model()
        cls.customer = account.objects.create_user("customer@staff-login.test", cls.password)
        cls.admin = account.objects.create_superuser("admin@staff-login.test", cls.password)
        cls.manager = account.objects.create_user(
            "manager@staff-login.test", cls.password, role=AccountRole.MANAGER,
        )

    def session_state(self, client):
        session = client.session
        return session.session_key, dict(session)

    def assert_customer_session(self, client, original_state, original_hash):
        self.assertEqual(self.session_state(client), original_state)
        self.assertEqual(client.session["_auth_user_id"], str(self.customer.pk))
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, AccountRole.CUSTOMER)
        self.assertEqual(self.customer.password, original_hash)

    def assert_denied_page(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/portal/login.html")
        self.assertTrue(response.context["access_denied"])
        self.assertFalse(response.context["form"].is_bound)
        self.assertFalse(response.context["form"].errors)
        self.assertContains(response, "Access Denied: Staff only.")

    def test_authenticated_customer_get_and_post_receive_denial_without_form_errors(self):
        self.client.force_login(self.customer)
        original_state = self.session_state(self.client)
        original_hash = self.customer.password
        for path in self.login_paths:
            for method in (self.client.get, self.client.post):
                with self.subTest(path=path, method=method.__name__):
                    self.assert_denied_page(method(path))
                    self.assert_customer_session(self.client, original_state, original_hash)

    @patch("apps.admin_portal.views.authenticate")
    def test_authenticated_customer_post_cannot_switch_to_submitted_admin_identity(self, authenticate):
        self.client.force_login(self.customer)
        original_state = self.session_state(self.client)
        original_hash = self.customer.password
        for path in self.login_paths:
            with self.subTest(path=path):
                response = self.client.post(path, {
                    "email": self.admin.email, "password": self.password,
                    "role": "ADMIN", "next": reverse("accounts_admin:list"),
                })
                self.assert_denied_page(response)
                self.assert_customer_session(self.client, original_state, original_hash)
                self.assertNotContains(response, self.admin.email)
        authenticate.assert_not_called()

    def test_customer_remains_forbidden_from_protected_admin_and_manager_routes(self):
        self.client.force_login(self.customer)
        original_state = self.session_state(self.client)
        original_hash = self.customer.password
        for path in (reverse("accounts_admin:list"), reverse("database_tools"),
                     reverse("catalog_admin:product_list")):
            for method in (self.client.get, self.client.post):
                with self.subTest(path=path, method=method.__name__):
                    self.assertEqual(method(path).status_code, 403)
                    self.assert_customer_session(self.client, original_state, original_hash)

    def test_anonymous_staff_login_get_has_no_required_field_errors(self):
        for path in self.login_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.context["form"].is_bound)
                self.assertFalse(response.context["form"].errors)
                self.assertFalse(response.context.get("access_denied"))
                self.assertNotContains(response, "Access Denied: Staff only.")

    def test_authenticated_customer_denial_post_still_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.customer)
        original_state = self.session_state(client)
        original_hash = self.customer.password
        for path in self.login_paths:
            with self.subTest(path=path):
                self.assertEqual(client.post(path).status_code, 403)
                self.assert_customer_session(client, original_state, original_hash)
                self.assert_denied_page(client.get(path))
                response = client.post(path, {
                    "email": self.admin.email, "password": self.password,
                    "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
                })
                self.assert_denied_page(response)
                self.assert_customer_session(client, original_state, original_hash)

    def test_anonymous_staff_login_post_preserves_csrf_and_role_destinations(self):
        client = Client(enforce_csrf_checks=True)
        for path in self.login_paths:
            for actor, destination in (
                (self.admin, reverse("accounts_admin:list")),
                (self.manager, reverse("catalog_admin:product_list")),
            ):
                with self.subTest(path=path, role=actor.role):
                    client.logout()
                    client.get(path)
                    data = {"email": actor.email, "password": self.password}
                    self.assertEqual(client.post(path, data).status_code, 403)
                    response = client.post(path, {
                        **data, "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
                    })
                    self.assertRedirects(response, destination, fetch_redirect_response=False)
                    self.assertEqual(client.session["_auth_user_id"], str(actor.pk))
