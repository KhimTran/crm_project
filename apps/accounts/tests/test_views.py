from django.contrib.auth import authenticate, get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.errors import AccountDeleteProtectedError


class AccountAdminViewTests(TestCase):
    password = "StrongPass!2026"

    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin@example.com", self.password)
        self.customer = get_user_model().objects.create_user("customer@example.com", self.password)
        self.list_url = reverse("accounts_admin:list")
        self.client.force_login(self.admin)

    def url(self, name, account=None):
        return reverse("accounts_admin:" + name, args=[(account or self.customer).pk])

    def test_routes_and_list_are_safe_paginated_and_filterable(self):
        self.assertEqual(self.list_url, "/admin-portal/accounts/")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.customer.password)
        self.assertNotContains(response, "password_hash")
        self.assertIn("last_login_at", response.context["page_obj"].object_list[0])
        self.assertEqual(response.context["page_obj"].paginator.count, 2)
        for number in range(21):
            get_user_model().objects.create_user(f"member{number}@example.com", self.password)
        self.assertEqual(len(self.client.get(self.list_url).context["page_obj"].object_list), 20)
        self.assertEqual(len(self.client.get(self.list_url + "?page=2").context["page_obj"].object_list), 3)
        filtered = self.client.get(self.list_url, {"role": "CUSTOMER", "status": "ACTIVE"})
        self.assertEqual(filtered.context["page_obj"].paginator.count, 22)
        invalid = self.client.get(self.list_url, {"role": "OTHER"})
        self.assertIsNone(invalid.context["page_obj"])
        self.assertIn("role", invalid.context["filters"].errors)

    def test_email_search_exact_partial_case_and_empty_query(self):
        search_cases = (
            ("customer@example.com", {self.customer.email}),
            ("customer", {self.customer.email}),
            ("CUSTOMER@EXAMPLE.COM", {self.customer.email}),
            ("@example.com", {self.admin.email, self.customer.email}),
            ("  customer  ", {self.customer.email}),
            ("missing", set()),
            ("   ", {self.admin.email, self.customer.email}),
        )
        for query, expected in search_cases:
            with self.subTest(query=query):
                response = self.client.get(self.list_url, {"q": query})
                self.assertEqual(response.status_code, 200)
                found = {account["email"] for account in response.context["page_obj"].object_list}
                self.assertEqual(found, expected)
                if not expected:
                    self.assertContains(response, "No accounts found.")
                    self.assertContains(response, "Create Account")
        self.assertContains(self.client.get(self.list_url, {"q": "customer"}), 'value="customer"')
        self.assertContains(self.client.get(self.list_url), 'name="q"')
        self.assertContains(self.client.get(self.list_url), ">Search</button>")

    def test_email_search_combines_with_role_and_status_filters(self):
        model = get_user_model()
        active_admin = model.objects.create_superuser("team.admin@search.test", self.password)
        active_customer = model.objects.create_user("team.customer@search.test", self.password)
        locked_admin = model.objects.create_superuser("locked.admin@search.test", self.password)
        locked_admin.status = AccountStatus.LOCKED
        locked_admin.save(update_fields=["status"])
        locked_customer = model.objects.create_user("locked.customer@search.test", self.password)
        locked_customer.status = AccountStatus.LOCKED
        locked_customer.save(update_fields=["status"])
        expected_cases = (
            ({"q": "@search.test", "role": "ADMIN"}, {active_admin.email, locked_admin.email}),
            ({"q": "@search.test", "role": "CUSTOMER"}, {active_customer.email, locked_customer.email}),
            ({"q": "@search.test", "status": "ACTIVE"}, {active_admin.email, active_customer.email}),
            ({"q": "@search.test", "status": "LOCKED"}, {locked_admin.email, locked_customer.email}),
            ({"q": "@search.test", "role": "customer", "status": "locked"}, {locked_customer.email}),
        )
        for params, expected in expected_cases:
            with self.subTest(params=params):
                response = self.client.get(self.list_url, params)
                self.assertEqual(response.status_code, 200)
                found = {account["email"] for account in response.context["page_obj"].object_list}
                self.assertEqual(found, expected)

    def test_email_search_pagination_preserves_search_and_filters(self):
        for number in range(21):
            get_user_model().objects.create_user(f"member{number}@search.test", self.password)
        for params, expected_link in (
            ({"q": "@search.test"}, "?page=2&amp;q=%40search.test"),
            ({"q": "@search.test", "role": "CUSTOMER", "status": "ACTIVE"},
             "?page=2&amp;q=%40search.test&amp;role=CUSTOMER&amp;status=ACTIVE"),
        ):
            with self.subTest(params=params):
                first_page = self.client.get(self.list_url, params)
                self.assertEqual(first_page.context["page_obj"].paginator.count, 21)
                self.assertContains(first_page, expected_link, html=False)
                second_page = self.client.get(self.list_url, params | {"page": "2"})
                self.assertEqual(len(second_page.context["page_obj"].object_list), 1)
                self.assertContains(second_page, "?page=1&amp;q=%40search.test")

    def test_detail_is_safe_and_missing_account_is_404(self):
        response = self.client.get(self.url("detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.customer.email)
        self.assertNotContains(response, self.customer.password)
        self.assertNotContains(response, "password_hash")
        self.assertEqual(self.client.get(reverse("accounts_admin:detail", args=[999999])).status_code, 404)

    def test_anonymous_customer_and_locked_admin_are_denied(self):
        routes = [self.list_url, self.url("detail"), reverse("accounts_admin:create"), self.url("reset_password")]
        self.client.logout()
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith("/admin-portal/login/?next="))
        self.client.force_login(self.customer)
        for route in routes:
            self.assertEqual(self.client.get(route).status_code, 403)
        self.client.force_login(self.admin)
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        for route in routes:
            self.assertEqual(self.client.get(route).status_code, 302)

    def test_mutations_require_active_admin(self):
        actions = [self.url("role"), self.url("lock"), self.url("unlock"), self.url("reset_password"), self.url("delete"), reverse("accounts_admin:create")]
        self.client.force_login(self.customer)
        for route in actions:
            self.assertEqual(self.client.post(route, {}).status_code, 403)
        self.client.force_login(self.admin)
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        for route in actions:
            self.assertEqual(self.client.post(route, {}).status_code, 302)

    def test_create_customer_and_admin_hashes_password(self):
        url = reverse("accounts_admin:create")
        for role in (AccountRole.CUSTOMER, AccountRole.ADMIN):
            email = f"new-{role.lower()}@example.com"
            response = self.client.post(url, {"email": email.upper(), "role": role, "status": "ACTIVE", "password": self.password, "password_confirm": self.password})
            self.assertEqual(response.status_code, 302)
            account = get_user_model().objects.get(email=email)
            self.assertEqual(account.role, role)
            self.assertNotEqual(account.password, self.password)
            self.assertTrue(account.check_password(self.password))

    def test_create_rejects_duplicate_invalid_role_status_mismatch_and_weak_password(self):
        url = reverse("accounts_admin:create")
        base = {"email": "fresh@example.com", "role": "CUSTOMER", "status": "ACTIVE", "password": self.password, "password_confirm": self.password}
        cases = [
            {"email": self.customer.email.upper()}, {"role": "MANAGER"},
            {"status": "DELETED"}, {"password_confirm": "Different!2026"},
            {"password": "123", "password_confirm": "123"},
        ]
        for change in cases:
            response = self.client.post(url, base | change)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        self.assertFalse(get_user_model().objects.filter(email="fresh@example.com").exists())

    def test_empty_post_payloads_are_validated(self):
        for url in (reverse("accounts_admin:create"), self.url("reset_password")):
            response = self.client.post(url, {})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)

    def test_email_edit_route_and_link_are_removed(self):
        path = f"/admin-portal/accounts/{self.customer.pk}/edit/"
        self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.post(path, {"email": "changed@example.com"}).status_code, 404)
        detail = self.client.get(self.url("detail"))
        self.assertContains(detail, self.customer.email)
        self.assertNotContains(detail, "Edit email")
        self.assertNotContains(detail, path)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.email, "customer@example.com")

    def test_html_create_role_and_filter_normalize_case(self):
        for index, (role, status) in enumerate((("admin", "active"), ("Customer", "Locked"))):
            response = self.client.post(reverse("accounts_admin:create"), {
                "email": f"case{index}@example.com", "role": role, "status": status,
                "password": self.password, "password_confirm": self.password,
            })
            self.assertEqual(response.status_code, 302)
            account = get_user_model().objects.get(email=f"case{index}@example.com")
            self.assertEqual((account.role, account.status), (role.upper(), status.upper()))
        filtered = self.client.get(self.list_url, {"role": "customer", "status": "locked"})
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.context["page_obj"].paginator.count, 1)
        self.assertEqual(self.client.post(self.url("role"), {"role": "Admin"}).status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, AccountRole.ADMIN)

    def test_role_action_is_post_only_and_preserves_final_admin(self):
        self.assertEqual(self.client.get(self.url("role")).status_code, 405)
        response = self.client.post(self.url("role"), {"role": "ADMIN"})
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, AccountRole.ADMIN)
        response = self.client.post(self.url("role", self.admin), {"role": "CUSTOMER"})
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, AccountRole.CUSTOMER)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(self.url("role"), {"role": "CUSTOMER"}).status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, AccountRole.ADMIN)

    def test_lock_unlock_post_only_and_self_lock_denied(self):
        self.assertEqual(self.client.get(self.url("lock")).status_code, 405)
        self.assertEqual(self.client.get(self.url("unlock")).status_code, 405)
        self.assertEqual(self.client.post(self.url("lock", self.admin)).status_code, 302)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.status, AccountStatus.ACTIVE)
        self.assertEqual(self.client.post(self.url("lock")).status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.status, AccountStatus.LOCKED)
        self.assertEqual(self.client.post(self.url("unlock")).status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.status, AccountStatus.ACTIVE)

    def test_reset_form_validation_and_password_change(self):
        url = self.url("reset_password")
        self.assertNotContains(self.client.get(url), "password_hash")
        for data in ({"new_password": "GoodPass!2026", "new_password_confirm": "Different!2026"}, {"new_password": "123", "new_password_confirm": "123"}):
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        new_password = "AnotherStrong!2026"
        response = self.client.post(url, {"new_password": new_password, "new_password_confirm": new_password})
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertIsNone(authenticate(email=self.customer.email, password=self.password))
        self.assertEqual(authenticate(email=self.customer.email, password=new_password), self.customer)
        self.assertNotContains(self.client.get(self.url("detail")), "password_hash")

    def test_delete_is_post_only_and_self_delete_denied(self):
        self.assertEqual(self.client.get(self.url("delete")).status_code, 405)
        self.assertEqual(self.client.post(self.url("delete", self.admin)).status_code, 302)
        self.assertTrue(get_user_model().objects.filter(pk=self.admin.pk).exists())
        self.assertEqual(self.client.post(self.url("delete")).status_code, 302)
        self.assertFalse(get_user_model().objects.filter(pk=self.customer.pk).exists())

    def test_csrf_is_enabled_for_mutations(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.url("lock")).status_code, 403)
        response = client.get(self.url("detail"))
        self.assertContains(response, "csrfmiddlewaretoken")
        token = client.cookies["csrftoken"].value
        self.assertEqual(client.post(self.url("lock"), {"csrfmiddlewaretoken": token}).status_code, 302)
