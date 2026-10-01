import json

from django.contrib.auth import authenticate, get_user_model
from django.test import Client, TestCase

from apps.accounts.constants import AccountRole, AccountStatus
from apps.customers.models import Customer


class AccountApiTests(TestCase):
    password = "StrongPass!2026"
    root = "/api/accounts/"

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin@example.test", self.password)
        self.customer = get_user_model().objects.create_user("customer@example.test", self.password)
        self.client.force_login(self.admin)

    def url(self, account=None, action=""):
        return f"{self.root}{(account or self.customer).pk}{action}"

    def send(self, method, url, data=None, client=None):
        if method == "get":
            return (client or self.client).get(url)
        return getattr(client or self.client, method)(
            url, data=json.dumps(data or {}), content_type="application/json"
        )

    def assert_safe(self, response):
        content = response.content.decode()
        self.assertNotIn("password_hash", content)
        self.assertNotIn('"password"', content)
        self.assertNotIn(self.password, content)

    def test_openapi_and_swagger_paths(self):
        self.assertEqual(self.client.get("/api/docs").status_code, 200)
        schema = self.client.get("/api/openapi.json")
        self.assertEqual(schema.status_code, 200)
        paths = schema.json()["paths"]
        self.assertTrue({
            "/api/accounts/", "/api/accounts/{account_id}",
            "/api/accounts/{account_id}/role", "/api/accounts/{account_id}/lock",
            "/api/accounts/{account_id}/unlock",
            "/api/accounts/{account_id}/reset-password",
        }.issubset(paths))
        self.assertEqual(set(paths["/api/accounts/"]), {"get", "post"})
        self.assertEqual(set(paths["/api/accounts/{account_id}"]), {"get", "delete"})

    def test_all_routes_reject_anonymous_customer_and_locked_admin(self):
        routes = [("get", self.root, None),
                  ("post", self.root, {"email": "fresh@example.test", "role": "CUSTOMER",
                                       "status": "ACTIVE", "password": self.password,
                                       "password_confirm": self.password}),
                  ("get", self.url(), None),
                  ("post", self.url(action="/role"), {"role": "ADMIN"}),
                  ("post", self.url(action="/lock"), None),
                  ("post", self.url(action="/unlock"), None),
                  ("post", self.url(action="/reset-password"),
                   {"new_password": self.password, "new_password_confirm": self.password}),
                  ("delete", self.url(), None)]
        self.client.logout()
        for method, url, data in routes:
            self.assertEqual(self.send(method, url, data).status_code, 401)
        self.client.force_login(self.customer)
        for method, url, data in routes:
            self.assertEqual(self.send(method, url, data).status_code, 403)
        self.client.force_login(self.admin)
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        for method, url, data in routes:
            self.assertIn(self.send(method, url, data).status_code, (401, 403))

    def test_list_detail_and_missing(self):
        response = self.client.get(self.root)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total"], 2)
        self.assertEqual(response.json()["items"][0]["account_id"], self.customer.pk)
        self.assert_safe(response)
        detail = self.client.get(self.url())
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["email"], self.customer.email)
        self.assert_safe(detail)
        self.assertEqual(self.client.get(f"{self.root}999999").status_code, 404)

    def test_create_and_validation(self):
        base = {"email": "NEW@EXAMPLE.TEST", "role": "CUSTOMER", "status": "ACTIVE",
                "password": self.password, "password_confirm": self.password}
        for role in ("CUSTOMER", "ADMIN"):
            payload = base | {"email": f"NEW-{role}@EXAMPLE.TEST", "role": role}
            response = self.send("post", self.root, payload)
            self.assertEqual(response.status_code, 201, response.content)
            self.assert_safe(response)
            account = get_user_model().objects.get(email=payload["email"].lower())
            self.assertTrue(account.check_password(self.password))
            self.assertEqual(account.role, role)
        invalid = [
            base | {"email": self.customer.email.upper()},
            base | {"email": "invalid-email"}, base | {"role": "INVALID"},
            base | {"status": "INVALID"}, base | {"password_confirm": "different"},
            base | {"password": "123", "password_confirm": "123"},
            base | {"password_hash": "secret"},
        ]
        for payload in invalid:
            response = self.send("post", self.root, payload)
            self.assertEqual(response.status_code, 400, response.content)
            self.assertNotIn("secret", response.content.decode())
            self.assert_safe(response)

    def test_email_patch_is_removed_and_role_is_dedicated(self):
        self.assertEqual(self.send("patch", self.url(), {"email": "UPDATED@EXAMPLE.TEST"}).status_code, 405)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.email, "customer@example.test")
        self.assertEqual(self.send("post", self.url(self.admin, "/role"), {"role": "CUSTOMER"}).status_code, 409)
        self.assertEqual(self.send("post", self.url(action="/role"), {"role": "ADMIN"}).status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, AccountRole.ADMIN)
        self.assertEqual(self.send("post", self.url(self.admin, "/role"), {"role": "CUSTOMER"}).status_code, 200)

    def test_case_insensitive_create_role_status_and_filters(self):
        base = {"status": "active", "password": self.password,
                "password_confirm": self.password}
        for index, (role, status) in enumerate((
            ("admin", "active"), ("Admin", "Locked"), ("ADMIN", "ACTIVE"),
            ("customer", "active"), ("Customer", "Locked"),
        )):
            response = self.send("post", self.root, base | {
                "email": f"variant{index}@example.test", "role": role, "status": status,
            })
            self.assertEqual(response.status_code, 201, response.content)
            self.assertEqual(response.json()["role"], role.upper())
            self.assertEqual(response.json()["status"], status.upper())
        for role in ("CUSTOMER", "customer", "Customer"):
            response = self.client.get(self.root, {"role": role})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["total"], 3)
        for status in ("ACTIVE", "active", "Active"):
            response = self.client.get(self.root, {"status": status})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["total"], 5)
        for query in ({"role": "MANAGER"}, {"status": "RUNNING"}):
            self.assertEqual(self.client.get(self.root, query).status_code, 400)

    def test_role_action_normalizes_case(self):
        for role in ("admin", "Customer", "Admin"):
            response = self.send("post", self.url(action="/role"), {"role": role})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["role"], role.upper())
            self.customer.refresh_from_db()
            self.assertEqual(self.customer.role, role.upper())
        self.assertEqual(self.send("post", self.url(action="/role"),
                                   {"role": "SUPERADMIN"}).status_code, 400)

    def test_lock_unlock_and_password_reset(self):
        self.assertEqual(self.send("post", self.url(self.admin, "/lock")).status_code, 409)
        self.assertEqual(self.send("post", self.url(action="/lock")).status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.status, AccountStatus.LOCKED)
        self.assertEqual(self.send("post", self.url(action="/lock")).status_code, 409)
        self.assertEqual(self.send("post", self.url(action="/unlock")).status_code, 200)
        new_password = "NewPassword!2026"
        response = self.send("post", self.url(action="/reset-password"),
                             {"new_password": new_password, "new_password_confirm": new_password})
        self.assertEqual(response.status_code, 200)
        self.assert_safe(response)
        self.assertIsNone(authenticate(email=self.customer.email, password=self.password))
        self.assertEqual(authenticate(email=self.customer.email, password=new_password).pk, self.customer.pk)
        self.assertEqual(self.send("post", self.url(action="/reset-password"),
                                   {"new_password": "123", "new_password_confirm": "123"}).status_code, 400)

    def test_delete_self_final_admin_and_safe_delete(self):
        self.assertEqual(self.send("delete", self.url(self.admin)).status_code, 409)
        self.assertEqual(self.send("delete", self.url()).status_code, 200)
        self.assertFalse(get_user_model().objects.filter(pk=self.customer.pk).exists())

    def test_fk_protected_delete_preserves_business_data(self):
        profile = Customer.objects.create(account=self.customer, full_name="Demo customer")
        response = self.send("delete", self.url())
        self.assertEqual(response.status_code, 409)
        self.assertNotIn("SQL", response.content.decode())
        self.assertTrue(get_user_model().objects.filter(pk=self.customer.pk).exists())
        self.assertTrue(Customer.objects.filter(pk=profile.pk, account=self.customer).exists())

    def test_csrf_session_mutations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        response = self.send("post", self.root, {"email": "csrf@example.test"}, client)
        self.assertEqual(response.status_code, 403)
        client.get("/api/docs")
        token = client.cookies["csrftoken"].value
        response = client.post(self.root, data=json.dumps({"email": "csrf@example.test"}),
                               content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 400)
