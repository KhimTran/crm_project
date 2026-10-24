import json

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import Client, TestCase

from apps.accounts.constants import AccountStatus


class SessionApiTests(TestCase):
    password = "StrongPass!2026"

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin@example.test", self.password)
        self.customer = get_user_model().objects.create_user("customer@example.test", self.password)
        self.client = Client(enforce_csrf_checks=True)

    def csrf(self):
        response = self.client.get("/api/auth/csrf")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", self.client.cookies)
        return response.json()["csrf_token"]

    def post(self, path, data=None, token=None):
        headers = {"HTTP_X_CSRFTOKEN": token} if token else {}
        return self.client.post(path, json.dumps(data or {}),
                                content_type="application/json", **headers)

    def login(self, email, password=None):
        return self.post("/api/auth/login", {"email": email,
                                             "password": password or self.password}, self.csrf())

    def test_admin_login_me_accounts_logout_sequence(self):
        self.assertEqual(self.client.get("/api/accounts/").status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        response = self.login(self.admin.email.upper())
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["authenticated"])
        self.assertEqual(response.json()["account"]["role"], "ADMIN")
        self.assertIn("sessionid", self.client.cookies)
        self.assertNotIn("session", response.json())
        self.assertNotIn("sessionid", response.content.decode())
        self.assertNotIn("password", response.content.decode())
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.admin.pk))
        me = self.client.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["account_id"], self.admin.pk)
        self.assertEqual(me.json()["status"], "ACTIVE")
        self.assertNotIn("password", me.content.decode())
        self.assertNotIn("password_hash", me.content.decode())
        self.assertEqual(self.client.get("/api/accounts/").status_code, 200)
        token = self.csrf()  # Django rotates the token during login.
        self.assertEqual(self.post("/api/auth/logout", token=token).status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.assertEqual(self.client.get("/api/accounts/").status_code, 401)

    def test_customer_can_log_in_but_cannot_manage_accounts(self):
        response = self.login(self.customer.email)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["account"]["role"], "CUSTOMER")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.assertEqual(self.client.get("/api/accounts/").status_code, 403)

    def test_bad_credentials_and_locked_account_fail_safely(self):
        for email, password in ((self.admin.email, "wrong"),
                                ("missing@example.test", self.password)):
            response = self.login(email, password)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()["detail"], "Invalid credentials")
            self.assertNotIn("sessionid", self.client.cookies)
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        response = self.login(self.admin.email)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid credentials")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_login_and_logout_require_csrf(self):
        payload = {"email": self.admin.email, "password": self.password}
        self.assertEqual(self.post("/api/auth/login", payload).status_code, 403)
        self.assertNotIn("sessionid", self.client.cookies)
        self.assertEqual(self.login(self.admin.email).status_code, 200)
        self.assertEqual(self.post("/api/auth/logout").status_code, 403)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 200)
        self.assertEqual(self.post("/api/auth/logout", token=self.csrf()).status_code, 200)

    def test_csrf_header_alone_does_not_authenticate(self):
        token = self.csrf()
        self.assertEqual(self.client.get("/api/accounts/", HTTP_X_CSRFTOKEN=token).status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me", HTTP_X_CSRFTOKEN=token).status_code, 401)

    def test_openapi_lists_auth_operations(self):
        paths = self.client.get("/api/openapi.json").json()["paths"]
        self.assertEqual(set(paths["/api/auth/csrf"]), {"get"})
        self.assertEqual(set(paths["/api/auth/login"]), {"post"})
        self.assertEqual(set(paths["/api/auth/me"]), {"get"})
        self.assertEqual(set(paths["/api/auth/logout"]), {"post"})
        docs = self.client.get("/api/docs")
        self.assertEqual(docs.status_code, 200)
        self.assertContains(docs, "accounts/swagger-session-init.js")
        self.assertTrue(finders.find("accounts/swagger-session-init.js"))
