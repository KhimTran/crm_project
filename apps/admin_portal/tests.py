from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.accounts.constants import AccountStatus


class AdminPortalUiTests(TestCase):
    password = "StrongPass!2026"

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin@example.test", self.password)
        self.customer = get_user_model().objects.create_user("customer@example.test", self.password)

    def test_login_root_and_safe_next(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email")
        self.assertContains(response, "Password")
        self.assertNotContains(response, "portal-sidebar")
        self.assertRedirects(self.client.get("/"), "/login/", fetch_redirect_response=False)
        response = self.client.get(reverse("accounts_admin:list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/?next="))
        response = self.client.post("/login/", {
            "email": self.admin.email.upper(), "password": self.password,
            "next": reverse("accounts_admin:list"),
        })
        self.assertRedirects(response, reverse("accounts_admin:list"), fetch_redirect_response=False)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.admin.pk))
        self.assertRedirects(self.client.get("/"), reverse("accounts_admin:list"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("accounts_admin:list")).status_code, 200)
        self.assertRedirects(self.client.get("/login/"), reverse("accounts_admin:list"), fetch_redirect_response=False)

    def test_login_rejects_invalid_customer_locked_and_unsafe_next(self):
        for email, password in ((self.admin.email, "wrong"),
                                ("missing@example.test", self.password),
                                (self.customer.email, self.password)):
            response = self.client.post("/login/", {"email": email, "password": password})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Unable to sign in")
            self.assertNotIn("sessionid", self.client.cookies)
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        response = self.client.post("/login/", {"email": self.admin.email, "password": self.password})
        self.assertContains(response, "Unable to sign in")
        self.admin.status = AccountStatus.ACTIVE
        self.admin.save(update_fields=["status"])
        response = self.client.post("/login/", {
            "email": self.admin.email, "password": self.password,
            "next": "https://example.org/elsewhere",
        })
        self.assertRedirects(response, reverse("accounts_admin:list"), fetch_redirect_response=False)

    def test_customer_and_locked_admin_cannot_access_portal(self):
        self.client.force_login(self.customer)
        for path in (reverse("accounts_admin:list"), reverse("database_tools")):
            self.assertEqual(self.client.get(path).status_code, 403)
        self.client.force_login(self.admin)
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        self.assertEqual(self.client.get(reverse("accounts_admin:list")).status_code, 302)

    def test_logout_is_post_csrf_and_invalidates_session(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.get("/logout/").status_code, 405)
        self.assertEqual(client.post("/logout/").status_code, 403)
        page = client.get(reverse("accounts_admin:list"))
        self.assertEqual(page.status_code, 200)
        token = client.cookies["csrftoken"].value
        self.assertRedirects(client.post("/logout/", {"csrfmiddlewaretoken": token}), "/login/", fetch_redirect_response=False)
        self.assertEqual(client.get(reverse("accounts_admin:list")).status_code, 302)

    def test_account_page_sidebar_modals_and_safe_content(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts_admin:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "portal-sidebar")
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, "mobileSidebar")
        self.assertContains(response, 'href="/admin-portal/accounts/"')
        self.assertNotContains(response, "Authorization")
        for modal_id, title in (("createModal", "Create Account"), ("roleModal", "Change Role"),
                                ("resetModal", "Reset Password"), ("confirmModal", "Confirm action")):
            self.assertContains(response, f'id="{modal_id}Title">{title}</h2></div>')
        self.assertContains(response, 'type="button" data-bs-dismiss="modal">Cancel</button>', count=4)
        for label in ("Create Account", "Change Role", "Reset Password", "Lock", "Delete", "Database Tools", "Products"):
            self.assertContains(response, label)
        self.assertContains(response, self.customer.email)
        self.assertNotContains(response, self.password)
        self.assertNotContains(response, "password_hash")
        self.assertNotContains(response, "Edit Account")
        self.assertNotContains(response, "Change Email")
        self.assertNotContains(response, 'href="#"')
        for library in ("bootstrap-icons", "font-awesome", "lucide", "material-icons"):
            self.assertNotContains(response, library)
        self.assertTrue(finders.find("favicon.svg"))
        self.assertTrue(finders.find("css/admin_portal.css"))
        self.assertTrue(finders.find("js/admin_portal.js"))

    def test_create_validation_and_account_actions_return_to_list(self):
        self.client.force_login(self.admin)
        create = reverse("accounts_admin:create")
        response = self.client.post(create, {
            "email": self.customer.email, "role": "CUSTOMER", "status": "ACTIVE",
            "password": self.password, "password_confirm": self.password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-reopen-modal="createModal"')
        self.assertTrue(response.context["create_form"].errors)
        response = self.client.post(create, {
            "email": "new@example.test", "role": "CUSTOMER", "status": "ACTIVE",
            "password": self.password, "password_confirm": self.password,
        })
        self.assertRedirects(response, reverse("accounts_admin:list"), fetch_redirect_response=False)
        target = get_user_model().objects.get(email="new@example.test")
        self.assertRedirects(self.client.post(reverse("accounts_admin:lock", args=[target.pk])), reverse("accounts_admin:list"), fetch_redirect_response=False)
        target.refresh_from_db()
        self.assertEqual(target.status, AccountStatus.LOCKED)
        page = self.client.get(reverse("accounts_admin:list"))
        self.assertContains(page, 'data-confirm-title="Unlock Account"')

    @override_settings(DEBUG=True)
    @patch("apps.admin_portal.views.call_command")
    def test_database_tools_seed_confirmation_and_unavailable_actions(self, command):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("database_tools"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seed Data")
        self.assertContains(response, "No callable Admin Portal backup or restore backend")
        self.assertNotContains(response, "Create Backup")
        self.assertNotContains(response, "Restore Database")
        self.assertEqual(self.client.post(reverse("seed_data"), {}).status_code, 302)
        command.assert_not_called()
        self.assertEqual(self.client.post(reverse("seed_data"), {"confirm": "SEED"}).status_code, 302)
        command.assert_called_once_with("seed_data", verbosity=0)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(reverse("seed_data"), {"confirm": "SEED"}).status_code, 403)

    @override_settings(DEBUG=False)
    def test_seed_ui_disabled_outside_development(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("database_tools"))
        self.assertNotContains(response, 'name="confirm"')
        self.assertEqual(self.client.post(reverse("seed_data"), {"confirm": "SEED"}).status_code, 403)
