import re
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.accounts.models import Account
from apps.customers.models import Customer


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CustomerAuthTests(TestCase):
    password = "StrongPass!2026"
    new_password = "NewStrongPass!2027"

    @classmethod
    def setUpTestData(cls):
        cls.customer = Account.objects.create_user("customer@auth.test", cls.password)
        cls.admin = Account.objects.create_superuser("admin@auth.test", cls.password)
        cls.manager = Account.objects.create_user("manager@auth.test", cls.password)
        cls.service = Account.objects.create_user("service@auth.test", cls.password)
        cls.manager.groups.add(Group.objects.create(name="CRM_MANAGER"))
        cls.service.groups.add(Group.objects.create(name="CUSTOMER_SERVICE"))
        Customer.objects.create(account=cls.customer, full_name="Customer")

    def sign_in(self, user=None, **extra):
        return self.client.post("/login/", {"email": (user or self.customer).email.upper(), "password": self.password, **extra})

    def test_login_redirects_by_role_and_groups_without_modifying_roles(self):
        for user, destination in ((self.customer, "/"), (self.admin, "/admin/"), (self.manager, "/crm/"), (self.service, "/crm/")):
            with self.subTest(user=user.email):
                self.client.logout()
                response = self.sign_in(user)
                self.assertRedirects(response, destination, fetch_redirect_response=False)
                self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
                user.refresh_from_db()
                self.assertIsNotNone(user.last_login)
                self.assertEqual(user.role, "ADMIN" if user == self.admin else "CUSTOMER")
        self.admin.groups.add(self.manager.groups.first())
        self.client.logout()
        self.assertRedirects(self.sign_in(self.admin), "/admin/", fetch_redirect_response=False)

    def test_wrong_password_never_discloses_locked_status_or_updates_last_login(self):
        Account.objects.filter(pk=self.customer.pk).update(status="LOCKED")
        for email in (self.customer.email, "missing@auth.test"):
            response = self.client.post("/login/", {"email": email, "password": "incorrect"})
            self.assertContains(response, "Email hoặc mật khẩu không đúng.")
            self.assertNotContains(response, "Tài khoản đã bị khóa")
            self.assertNotIn("_auth_user_id", self.client.session)
        response = self.sign_in()
        self.assertContains(response, "Tài khoản đã bị khóa")
        self.customer.refresh_from_db()
        self.assertIsNone(self.customer.last_login)

    def test_next_accepts_local_authorized_get_destinations_with_filters(self):
        self.assertRedirects(self.sign_in(next="/products/?min_price=100"), "/products/?min_price=100", fetch_redirect_response=False)
        self.client.logout()
        self.assertRedirects(self.sign_in(next="/account/profile/"), "/account/profile/", fetch_redirect_response=False)
        self.client.logout()
        self.assertRedirects(self.sign_in(self.manager, next="/crm/"), "/crm/", fetch_redirect_response=False)

    def test_next_blocks_external_auth_loops_unknown_paths_and_unowned_area(self):
        for destination in ("https://evil.example/", "//evil.example/", "/\\evil.example/", "/login/", "/logout/", "/register/",
                            "/admin-portal/", "/crm/", "/missing/", "/password/reset/", "/login/?next=/login/"):
            with self.subTest(next=destination):
                self.client.logout()
                self.assertRedirects(self.sign_in(next=destination), "/", fetch_redirect_response=False)
        self.assertRedirects(self.client.get("/login/?next=/login/"), "/", fetch_redirect_response=False)

    def test_crm_authorization_and_old_sessions_after_lock_or_group_revocation(self):
        self.assertRedirects(self.client.get("/crm/"), "/login/?next=/crm/", fetch_redirect_response=False)
        self.client.force_login(self.customer)
        self.assertRedirects(self.client.get("/crm/"), "/", fetch_redirect_response=False)
        for user in (self.admin, self.manager, self.service):
            self.client.force_login(user)
            self.assertContains(self.client.get("/crm/"), "Sắp có")
        self.client.force_login(self.manager)
        self.manager.groups.clear()
        self.assertRedirects(self.client.get("/crm/"), "/", fetch_redirect_response=False)
        self.client.force_login(self.customer)
        Account.objects.filter(pk=self.customer.pk).update(status="LOCKED")
        for path in ("/account/profile/", "/account/password/change/", "/crm/"):
            self.assertEqual(self.client.get(path).status_code, 302)
            self.assertEqual(self.client.post(path, {}).status_code, 302)

    def test_registration_field_errors_and_privilege_payload(self):
        data = {"email": " NEW@AUTH.TEST ", "password": self.password, "password_confirm": self.password,
                "full_name": "New customer", "role": "ADMIN", "status": "LOCKED", "groups": "CRM_MANAGER", "permissions": "*"}
        self.assertRedirects(self.client.post("/register/", data), "/login/", fetch_redirect_response=False)
        account = Account.objects.get(email="new@auth.test")
        self.assertEqual((account.role, account.status), ("CUSTOMER", "ACTIVE"))
        self.assertFalse(account.groups.exists())
        self.assertTrue(account.check_password(self.password))
        self.assertTrue(Customer.objects.filter(account=account).exists())
        duplicate = self.client.post("/register/", data)
        self.assertIn("email", duplicate.context["form"].errors)
        weak = self.client.post("/register/", {**data, "email": "weak@auth.test", "password": "123", "password_confirm": "456"})
        self.assertIn("password", weak.context["form"].errors)
        self.assertIn("password_confirm", weak.context["form"].errors)
        self.assertFalse(Account.objects.filter(email="weak@auth.test").exists())

    def test_password_change_requires_current_password_preserves_current_session_invalidates_other(self):
        self.client.force_login(self.customer)
        other = Client()
        other.force_login(self.customer)
        data = {"old_password": "wrong", "new_password1": self.new_password, "new_password2": self.new_password}
        response = self.client.post("/account/password/change/", data)
        self.assertIn("old_password", response.context["form"].errors)
        weak = self.client.post("/account/password/change/", {**data, "old_password": self.password, "new_password1": "123", "new_password2": "123"})
        self.assertTrue(weak.context["form"].errors)
        mismatch = self.client.post("/account/password/change/", {**data, "old_password": self.password, "new_password2": "Mismatch!2026"})
        self.assertTrue(mismatch.context["form"].errors)
        self.assertRedirects(self.client.post("/account/password/change/", {**data, "old_password": self.password}), "/", fetch_redirect_response=False)
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.check_password(self.password))
        self.assertTrue(self.customer.check_password(self.new_password))
        self.assertEqual(self.client.get("/account/profile/").status_code, 200)
        self.assertEqual(other.get("/account/profile/").status_code, 302)

    def test_reset_response_does_not_disclose_email_and_skips_locked_accounts(self):
        for email, sent in (("missing@auth.test", 0), (self.customer.email.upper(), 1)):
            response = self.client.post("/password/reset/", {"email": email})
            self.assertRedirects(response, "/password/reset/done/", fetch_redirect_response=False)
            self.assertEqual(len(mail.outbox), sent)
        Account.objects.filter(pk=self.customer.pk).update(status="LOCKED")
        self.assertRedirects(self.client.post("/password/reset/", {"email": self.customer.email}), "/password/reset/done/", fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(self.password, mail.outbox[0].body)
        self.assertNotIn(self.customer.password, mail.outbox[0].body)

    def reset_link(self):
        self.client.post("/password/reset/", {"email": self.customer.email})
        return re.search(r"http://testserver([^\s]+)", mail.outbox[-1].body).group(1)

    def test_reset_token_changes_password_invalidates_sessions_and_cannot_be_reused(self):
        old_session = Client()
        old_session.force_login(self.customer)
        link = self.reset_link()
        start = self.client.get(link)
        self.assertEqual(start.status_code, 302)
        self.assertIn("set-password", start.url)
        form_path = start.url
        self.assertContains(self.client.get(form_path), "Lưu mật khẩu mới")
        weak = self.client.post(form_path, {"new_password1": "123", "new_password2": "123"})
        self.assertTrue(weak.context["form"].errors)
        self.assertRedirects(self.client.post(form_path, {"new_password1": self.new_password, "new_password2": self.new_password}),
                             "/password/reset/complete/", fetch_redirect_response=False)
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.check_password(self.new_password))
        self.assertFalse(self.customer.check_password(self.password))
        self.assertEqual(old_session.get("/account/profile/").status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(self.client.get(link), "không còn hợp lệ")
        self.assertRedirects(self.sign_in(password=self.new_password), "/", fetch_redirect_response=False)

    def test_reset_invalid_expired_and_locked_tokens_are_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.customer.pk))
        self.assertContains(self.client.get(f"/password/reset/{uid}/bad-token/"), "không còn hợp lệ")
        token = default_token_generator.make_token(self.customer)
        link = f"/password/reset/{uid}/{token}/"
        with patch.object(default_token_generator, "_now", return_value=default_token_generator._now() + timedelta(hours=2)):
            self.assertContains(self.client.get(link), "không còn hợp lệ")
        # A lock after opening the link also prevents the actual password write.
        start = self.client.get(link)
        Account.objects.filter(pk=self.customer.pk).update(status="LOCKED")
        response = self.client.post(start.url, {"new_password1": self.new_password, "new_password2": self.new_password})
        self.assertContains(response, "không còn hợp lệ")
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.check_password(self.password))

    def test_csrf_for_login_register_logout_profile_password_change_and_reset(self):
        client = Client(enforce_csrf_checks=True)
        for path in ("/login/", "/register/", "/logout/", "/password/reset/"):
            self.assertEqual(client.post(path, {}).status_code, 403)
        page = client.get("/login/")
        self.assertEqual(page.status_code, 200)
        token = client.cookies["csrftoken"].value
        response = client.post("/login/", {"email": self.customer.email, "password": self.password, "csrfmiddlewaretoken": token})
        self.assertEqual(response.status_code, 302)
        for path in ("/account/profile/", "/account/password/change/", "/logout/"):
            self.assertEqual(client.post(path, {}).status_code, 403)
        self.assertEqual(client.get("/logout/").status_code, 405)
        token = client.cookies["csrftoken"].value
        self.assertRedirects(client.post("/logout/", {"csrfmiddlewaretoken": token}), "/login/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", client.session)

    def test_reset_confirm_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        uid = urlsafe_base64_encode(force_bytes(self.customer.pk))
        token = default_token_generator.make_token(self.customer)
        start = client.get(f"/password/reset/{uid}/{token}/")
        client.get(start.url)
        data = {"new_password1": self.new_password, "new_password2": self.new_password}
        self.assertEqual(client.post(start.url, data).status_code, 403)
        self.assertEqual(client.post(start.url, {**data, "csrfmiddlewaretoken": client.cookies["csrftoken"].value}).status_code, 302)

    def test_customer_login_route_and_staff_portal_separation(self):
        manager = Account.objects.create_user("role-manager@auth.test", self.password, role="MANAGER")
        # Customer login route uses customer template
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/customer/login.html")

        # Staff login routes use shared staff login template
        for staff_path in ("/admin/login/", "/manager/login/"):
            with self.subTest(path=staff_path):
                response = self.client.get(staff_path)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "admin/portal/login.html")

        # Staff login routes redirect admin and manager to their respective dashboards
        self.assertRedirects(
            self.client.post("/admin/login/", {"email": self.admin.email, "password": self.password}),
            reverse("accounts_admin:list"), fetch_redirect_response=False,
        )
        self.client.logout()
        self.assertRedirects(
            self.client.post("/manager/login/", {
                "email": manager.email, "password": self.password,
                "next": "/manager/catalog/products/999/edit/",
            }),
            "/manager/catalog/products/999/edit/", fetch_redirect_response=False,
        )
        self.client.logout()

        # Customer login route redirects staff roles appropriately
        self.assertRedirects(self.client.post("/login/", {
            "email": manager.email, "password": self.password, "next": "/admin/accounts/",
        }), "/manager/", fetch_redirect_response=False)

    def test_customer_denied_from_staff_portal_login(self):
        # Customer credentials submitted to staff portal login are denied
        response = self.client.post("/admin/login/", {"email": self.customer.email, "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access Denied: Staff only.")
        self.assertNotIn("_auth_user_id", self.client.session)


class ManagerPasswordChangeTests(TestCase):
    password = "StrongPass!2026"
    new_password = "NewStrongPass!2027"
    path = "/account/password/change/"

    @classmethod
    def setUpTestData(cls):
        cls.manager = Account.objects.create_user("manager@password.test", cls.password, role="MANAGER")
        cls.other_account = Account.objects.create_user("other@password.test", cls.password)

    def password_data(self, **extra):
        return {"old_password": self.password, "new_password1": self.new_password,
                "new_password2": self.new_password, **extra}

    def test_manager_login_redirects_and_password_change_next(self):
        for login_path, extra, destination in (
            ("/login/", {}, "/manager/"),
            ("/login/", {"next": self.path}, self.path),
            ("/manager/login/", {}, reverse("catalog_admin:product_list")),
        ):
            with self.subTest(login_path=login_path, extra=extra):
                self.client.logout()
                response = self.client.post(login_path, {
                    "email": self.manager.email, "password": self.password, **extra,
                })
                self.assertRedirects(response, destination, fetch_redirect_response=False)
                self.assertEqual(self.client.get(self.path).status_code, 200)
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.role, "MANAGER")
        self.assertTrue(self.manager.check_password(self.password))

    def test_manager_password_change_requires_current_password_and_valid_new_password(self):
        self.client.force_login(self.manager)
        original_hash = self.manager.password
        for data, error_field in (
            (self.password_data(old_password="wrong"), "old_password"),
            (self.password_data(new_password1="123", new_password2="123"), "new_password2"),
            (self.password_data(new_password2="Mismatch!2026"), "new_password2"),
        ):
            with self.subTest(error_field=error_field):
                response = self.client.post(self.path, data)
                self.assertEqual(response.status_code, 200)
                self.assertIn(error_field, response.context["form"].errors)
                self.manager.refresh_from_db()
                self.assertEqual(self.manager.password, original_hash)
                self.assertEqual(self.client.session["_auth_user_id"], str(self.manager.pk))

    def test_manager_changes_only_self_and_preserves_current_session_invalidates_others(self):
        self.client.force_login(self.manager)
        other_session = Client()
        other_session.force_login(self.manager)
        other_hash = self.other_account.password
        response = self.client.post(self.path, self.password_data(
            account_id=self.other_account.pk, email=self.other_account.email,
            role="ADMIN", status="LOCKED", next="/admin/",
        ))
        self.assertRedirects(response, "/manager/", fetch_redirect_response=False)
        self.manager.refresh_from_db()
        self.other_account.refresh_from_db()
        self.assertTrue(self.manager.check_password(self.new_password))
        self.assertFalse(self.manager.check_password(self.password))
        self.assertEqual((self.manager.role, self.manager.status), ("MANAGER", "ACTIVE"))
        self.assertEqual(self.other_account.password, other_hash)
        self.assertEqual(self.client.session["_auth_user_id"], str(self.manager.pk))
        self.assertEqual(self.client.get(reverse("catalog_admin:product_list")).status_code, 200)
        self.assertRedirects(other_session.get(self.path), f"/login/?next={self.path}", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", other_session.session)
        self.client.logout()
        self.assertEqual(self.client.post("/login/", {
            "email": self.manager.email, "password": self.password,
        }).status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(self.client.post("/login/", {
            "email": self.manager.email, "password": self.new_password,
        }), "/manager/", fetch_redirect_response=False)

    def test_locked_manager_cannot_change_password_from_existing_session(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(self.path).status_code, 200)
        original_hash = self.manager.password
        Account.objects.filter(pk=self.manager.pk).update(status="LOCKED")
        for method, data in ((self.client.get, {}), (self.client.post, self.password_data())):
            response = method(self.path, data)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("/login/?next="))
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.password, original_hash)
        self.assertRedirects(self.client.get(reverse("catalog_admin:product_list")),
                             "/manager/login/?next=%2Fmanager%2Fcatalog%2Fproducts%2F",
                             fetch_redirect_response=False)
        self.client.logout()
        response = self.client.post("/manager/login/", {
            "email": self.manager.email, "password": self.password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_manager_password_change_requires_csrf_and_post_to_write(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.manager)
        self.assertEqual(client.get(self.path).status_code, 200)
        self.assertEqual(client.post(self.path, self.password_data()).status_code, 403)
        for method in (client.put, client.patch, client.delete):
            self.assertEqual(method(self.path, HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value).status_code, 405)
        self.manager.refresh_from_db()
        self.assertTrue(self.manager.check_password(self.password))
        response = client.post(self.path, self.password_data(
            csrfmiddlewaretoken=client.cookies["csrftoken"].value,
        ))
        self.assertRedirects(response, "/manager/", fetch_redirect_response=False)
        self.manager.refresh_from_db()
        self.assertTrue(self.manager.check_password(self.new_password))

    def test_anonymous_password_change_requires_login(self):
        for method, data in ((self.client.get, {}), (self.client.post, self.password_data())):
            self.assertRedirects(method(self.path, data),
                                 f"/login/?next={self.path}", fetch_redirect_response=False)
        self.manager.refresh_from_db()
        self.assertTrue(self.manager.check_password(self.password))
