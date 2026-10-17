from unittest.mock import patch
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.accounts.constants import AccountRole, AccountStatus


class AdminPortalUiTests(TestCase):
    password = "StrongPass!2026"

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin@example.test", self.password)
        self.manager = get_user_model().objects.create_user("manager@example.test", self.password, role=AccountRole.MANAGER)
        self.customer = get_user_model().objects.create_user("customer@example.test", self.password)

    def test_login_root_and_safe_next(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email")
        self.assertContains(response, "Password")
        self.assertNotContains(response, "portal-sidebar")
        self.assertRedirects(self.client.get("/admin/"), "/admin/login/", fetch_redirect_response=False)
        response = self.client.get(reverse("accounts_admin:list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/admin/login/?next="))
        response = self.client.post("/admin/login/", {
            "email": self.admin.email.upper(), "password": self.password,
            "next": reverse("accounts_admin:list"),
        })
        self.assertRedirects(response, reverse("accounts_admin:list"), fetch_redirect_response=False)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.admin.pk))
        self.assertRedirects(self.client.get("/admin/"), reverse("accounts_admin:list"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("accounts_admin:list")).status_code, 200)
        self.assertRedirects(self.client.get("/admin/login/"), reverse("accounts_admin:list"), fetch_redirect_response=False)

    def test_login_rejects_invalid_customer_locked_and_unsafe_next(self):
        # Invalid credentials or missing account
        for email, password in ((self.admin.email, "wrong"),
                                ("missing@example.test", self.password)):
            response = self.client.post("/admin/login/", {"email": email, "password": password})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Unable to sign in")
            self.assertNotIn("sessionid", self.client.cookies)

        # Customer is denied staff access
        response = self.client.post("/admin/login/", {"email": self.customer.email, "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access Denied: Staff only.")
        self.assertNotIn("sessionid", self.client.cookies)

        # Manager can sign in at shared staff login and is redirected to manager dashboard
        response = self.client.post("/admin/login/", {"email": self.manager.email, "password": self.password})
        self.assertRedirects(response, reverse("catalog_admin:product_list"), fetch_redirect_response=False)
        self.client.logout()

        # Locked admin cannot sign in
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        response = self.client.post("/admin/login/", {"email": self.admin.email, "password": self.password})
        self.assertContains(response, "Unable to sign in")
        self.admin.status = AccountStatus.ACTIVE
        self.admin.save(update_fields=["status"])

        # Unsafe external next or forbidden manager next safely redirects to admin list
        for bad_next in ("https://example.org/elsewhere", "/manager/catalog/products/"):
            response = self.client.post("/admin/login/", {
                "email": self.admin.email, "password": self.password,
                "next": bad_next,
            })
            self.assertRedirects(response, reverse("accounts_admin:list"), fetch_redirect_response=False)
            self.client.logout()

        # Authorized admin next redirects to the requested admin page
        response = self.client.post("/admin/login/", {
            "email": self.admin.email, "password": self.password,
            "next": reverse("database_tools"),
        })
        self.assertRedirects(response, reverse("database_tools"), fetch_redirect_response=False)

    def test_customer_manager_and_locked_admin_cannot_access_portal(self):
        self.client.force_login(self.customer)
        for path in (reverse("accounts_admin:list"), reverse("database_tools")):
            self.assertEqual(self.client.get(path).status_code, 403)
        self.client.force_login(self.manager)
        for path in (reverse("accounts_admin:list"), reverse("database_tools")):
            self.assertEqual(self.client.get(path).status_code, 403)
        self.client.force_login(self.admin)
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        self.assertEqual(self.client.get(reverse("accounts_admin:list")).status_code, 302)

    def test_logout_is_post_csrf_and_invalidates_session(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.get("/admin/logout/").status_code, 405)
        self.assertEqual(client.post("/admin/logout/").status_code, 403)
        page = client.get(reverse("accounts_admin:list"))
        self.assertEqual(page.status_code, 200)
        token = client.cookies["csrftoken"].value
        self.assertRedirects(client.post("/admin/logout/", {"csrfmiddlewaretoken": token}), "/admin/login/", fetch_redirect_response=False)
        self.assertEqual(client.get(reverse("accounts_admin:list")).status_code, 302)

    def test_account_page_sidebar_modals_and_safe_content(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts_admin:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "portal-sidebar")
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, "mobileSidebar")
        self.assertContains(response, 'href="/admin/accounts/"')
        self.assertNotContains(response, "Authorization")
        for modal_id, title in (("createModal", "Create Account"), ("roleModal", "Change Role"),
                                ("resetModal", "Reset Password"), ("confirmModal", "Confirm action")):
            self.assertContains(response, f'id="{modal_id}Title">{title}</h2></div>')
        self.assertContains(response, 'type="button" data-bs-dismiss="modal">Cancel</button>', count=4)
        for label in ("Create Account", "Change Role", "Reset Password", "Lock", "Delete", "Database Tools"):
            self.assertContains(response, label)
        # Products and other catalog/crm modules are moved to Manager UI
        self.assertNotContains(response, "catalog_admin:product_list")
        self.assertContains(response, self.customer.email)
        self.assertNotContains(response, self.password)
        self.assertNotContains(response, "password_hash")
        self.assertNotContains(response, "Edit Account")
        self.assertNotContains(response, "Change Email")
        self.assertNotContains(response, 'href="#"')
        for library in ("bootstrap-icons", "font-awesome", "lucide", "material-icons"):
            self.assertNotContains(response, library)
        self.assertContains(response, 'portal-badge role-admin')
        self.assertContains(response, 'portal-badge role-manager')
        self.assertContains(response, 'portal-badge role-customer')
        self.assertContains(response, '<option value="MANAGER">MANAGER</option>')
        self.assertTrue(finders.find("favicon.svg"))
        css_path = finders.find("css/admin_portal.css")
        self.assertTrue(css_path)
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
            self.assertIn(".portal-badge.role-manager", css_content)
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
    def test_database_tools_seed_confirmation(self, command):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("database_tools"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Database Backup")
        self.assertContains(response, "Create Backup Now")
        self.assertContains(response, "Development Seed Data")
        self.assertEqual(self.client.post(reverse("seed_data"), {}).status_code, 302)
        command.assert_not_called()
        self.assertEqual(self.client.post(reverse("seed_data"), {"confirm": "SEED"}).status_code, 302)
        command.assert_called_once_with("seed_data", verbosity=0)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(reverse("seed_data"), {"confirm": "SEED"}).status_code, 403)

    @patch("apps.admin_portal.views.create_database_backup")
    def test_database_backup_view(self, mock_create_backup):
        from pathlib import Path
        mock_create_backup.return_value = Path("test_backup.sql")
        self.client.force_login(self.admin)
        response = self.client.post(reverse("database_backup"))
        self.assertRedirects(response, reverse("database_tools"))
        mock_create_backup.assert_called_once_with(actor_id=self.admin.pk)

        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(reverse("database_backup")).status_code, 403)

    @patch("apps.admin_portal.views.restore_database_from_backup")
    def test_database_restore_view(self, mock_restore):
        self.client.force_login(self.admin)
        # Without confirmation
        response = self.client.post(reverse("database_restore"), {"filename": "test.sql", "confirm": "WRONG"})
        self.assertRedirects(response, reverse("database_tools"))
        mock_restore.assert_not_called()

        # Exact file/database confirmation and maintenance acknowledgment are required.
        mock_restore.return_value = Path("recovery.sql")
        database_name = settings.DATABASES["default"]["NAME"]
        response = self.client.post(reverse("database_restore"), {
            "filename": "test.sql", "confirm": f"RESTORE test.sql TO {database_name}",
            "target_database": database_name, "maintenance_ack": "on",
        })
        self.assertContains(response, "Recovery backup retained")
        mock_restore.assert_called_once_with(
            "test.sql", f"RESTORE test.sql TO {database_name}", actor=self.admin,
            target_database=database_name, maintenance_ack=True,
        )

        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(reverse("database_restore"), {"filename": "test.sql", "confirm": "RESTORE"}).status_code, 403)

    @override_settings(DEBUG=False)
    def test_seed_ui_disabled_outside_development(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("database_tools"))
        self.assertNotContains(response, 'name="confirm"')
        self.assertEqual(self.client.post(reverse("seed_data"), {"confirm": "SEED"}).status_code, 403)


class ManagerPortalUiTests(TestCase):
    password = "StrongPass!2026"

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin@manager-tests.test", self.password)
        self.manager = get_user_model().objects.create_user("manager@manager-tests.test", self.password, role=AccountRole.MANAGER)
        self.customer = get_user_model().objects.create_user("customer@manager-tests.test", self.password)

    def test_manager_login_and_home_routing(self):
        response = self.client.get("/manager/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CRM STAFF PORTAL")
        self.assertContains(response, "Email")
        self.assertContains(response, "Password")
        # Unauthenticated /manager/ redirects to /manager/login/
        self.assertRedirects(self.client.get("/manager/"), "/manager/login/", fetch_redirect_response=False)
        # Successful manager login
        response = self.client.post("/manager/login/", {
            "email": self.manager.email.upper(), "password": self.password,
        })
        self.assertRedirects(response, reverse("catalog_admin:product_list"), fetch_redirect_response=False)
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.manager.pk))
        self.client.logout()

        # Admin signing in via /manager/login/ is redirected to Admin dashboard
        response = self.client.post("/manager/login/", {
            "email": self.admin.email, "password": self.password,
        })
        self.assertRedirects(response, reverse("accounts_admin:list"), fetch_redirect_response=False)
        self.client.logout()

        # Manager signing in with valid manager next URL
        response = self.client.post("/manager/login/", {
            "email": self.manager.email, "password": self.password,
            "next": "/manager/catalog/categories/",
        })
        self.assertRedirects(response, "/manager/catalog/categories/", fetch_redirect_response=False)
        self.client.logout()

        # Manager signing in with forbidden admin next URL safely falls back to manager dashboard
        response = self.client.post("/manager/login/", {
            "email": self.manager.email, "password": self.password,
            "next": reverse("accounts_admin:list"),
        })
        self.assertRedirects(response, reverse("catalog_admin:product_list"), fetch_redirect_response=False)

    def test_manager_login_rejects_customer_and_locked_manager(self):
        response = self.client.post("/manager/login/", {"email": self.customer.email, "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access Denied: Staff only.")
        self.assertNotIn("_auth_user_id", self.client.session)

        self.manager.status = AccountStatus.LOCKED
        self.manager.save(update_fields=["status"])
        response = self.client.post("/manager/login/", {"email": self.manager.email, "password": self.password})
        self.assertContains(response, "Unable to sign in")

    def test_manager_ui_has_catalog_and_crm_modules_and_no_admin_tools(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("catalog_admin:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CRM Manager Portal")
        # Manager sidebar modules
        for label in ("Products", "Suppliers", "Categories", "Brands", "Customers", "Customer Report", "Feedback", "Surveys"):
            self.assertContains(response, label)
        # Admin features must be cleaned up / absent from Manager UI
        self.assertNotContains(response, "accounts_admin:list")
        self.assertNotContains(response, "database_tools")
        self.assertNotContains(response, "Database Tools")
        self.assertNotContains(response, "Create Account")

    def test_manager_logout_is_post_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manager)
        self.assertEqual(client.get("/manager/logout/").status_code, 405)
        self.assertEqual(client.post("/manager/logout/").status_code, 403)
        page = client.get(reverse("catalog_admin:product_list"))
        self.assertEqual(page.status_code, 200)
        token = client.cookies["csrftoken"].value
        response = client.post("/manager/logout/", {"csrfmiddlewaretoken": token})
        self.assertRedirects(response, "/manager/login/", fetch_redirect_response=False)
