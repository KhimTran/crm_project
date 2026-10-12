from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

from django.contrib import messages
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.decorators import get_home_path, role_required
from apps.accounts.models import Account


class RoleRequiredTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        password = "StrongPass!2026"
        cls.admin = Account.objects.create_superuser("admin@roles.test", password)
        cls.customer = Account.objects.create_user("customer@roles.test", password)
        cls.manager = Account.objects.create_user("manager@roles.test", password)
        cls.service = Account.objects.create_user("service@roles.test", password)
        cls.manager_group = Group.objects.create(name="CRM_MANAGER")
        cls.service_group = Group.objects.create(name="CUSTOMER_SERVICE")
        cls.manager.groups.add(cls.manager_group)
        cls.service.groups.add(cls.service_group)

    def setUp(self):
        self.factory = RequestFactory()
        self.view = Mock(return_value=HttpResponse("Protected content"))

    def request(self, user, path="/protected/"):
        request = self.factory.get(path)
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_anonymous_redirect_uses_login_url_and_preserves_full_next(self):
        request = self.request(AnonymousUser(), "/protected/?page=2&query=badminton")
        response = role_required("ADMIN")(self.view)(request)
        self.assertEqual(response.status_code, 302)
        url = urlsplit(response.url)
        self.assertEqual(url.path, "/login/")
        self.assertEqual(parse_qs(url.query)["next"], [request.get_full_path()])
        self.view.assert_not_called()

    @override_settings(LOGIN_URL="/customer-sign-in/?source=shop")
    def test_anonymous_redirect_honors_overridden_settings(self):
        response = role_required("CUSTOMER")(self.view)(self.request(AnonymousUser()))
        url = urlsplit(response.url)
        self.assertEqual(url.path, "/customer-sign-in/")
        self.assertEqual(parse_qs(url.query), {"source": ["shop"], "next": ["/protected/"]})
        self.view.assert_not_called()

    @override_settings(LOGIN_URL="login")
    def test_anonymous_redirect_accepts_named_login_url(self):
        response = role_required("CUSTOMER")(self.view)(self.request(AnonymousUser()))
        self.assertEqual(urlsplit(response.url).path, "/admin-portal/login/")

    def test_admin_can_access_admin_view(self):
        request = self.request(self.admin)
        response = role_required("ADMIN")(self.view)(request)
        self.assertEqual(response.status_code, 200)
        self.view.assert_called_once_with(request)

    def test_customer_can_access_customer_view(self):
        request = self.request(self.customer)
        response = role_required("CUSTOMER")(self.view)(request)
        self.assertEqual(response.status_code, 200)
        self.view.assert_called_once_with(request)

    def test_wrong_role_adds_vietnamese_message_and_redirects_home(self):
        for user, permission, destination in (
            (self.customer, "ADMIN", "/"),
            (self.manager, "ADMIN", "/crm/"),
            (self.service, "ADMIN", "/crm/"),
            (self.admin, "CUSTOMER", "/admin-portal/"),
        ):
            with self.subTest(permission=permission, user=user.email):
                request = self.request(user)
                response = role_required(permission)(self.view)(request)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, destination)
                stored = list(messages.get_messages(request))
                self.assertEqual([str(message) for message in stored], [
                    "Bạn không có quyền truy cập chức năng này.",
                ])
                self.assertEqual(stored[0].level, messages.ERROR)
        self.view.assert_not_called()

    def test_crm_manager_group_allows_manager_view(self):
        request = self.request(self.manager)
        response = role_required("CRM_MANAGER")(self.view)(request)
        self.assertEqual(self.manager.role, AccountRole.CUSTOMER)
        self.assertEqual(response.status_code, 200)
        self.view.assert_called_once_with(request)

    def test_customer_service_group_allows_service_view(self):
        request = self.request(self.service)
        response = role_required("CUSTOMER_SERVICE")(self.view)(request)
        self.assertEqual(response.status_code, 200)
        self.view.assert_called_once_with(request)

    def test_multiple_allowed_groups_accept_either_membership(self):
        protected = role_required("CRM_MANAGER", "CUSTOMER_SERVICE")(self.view)
        for user in (self.manager, self.service):
            with self.subTest(user=user.email):
                self.assertEqual(protected(self.request(user)).status_code, 200)
        self.assertEqual(self.view.call_count, 2)

    def test_multiple_allowed_roles_accept_role_or_group(self):
        protected = role_required("ADMIN", "CRM_MANAGER")(self.view)
        for user in (self.admin, self.manager):
            with self.subTest(user=user.email):
                self.assertEqual(protected(self.request(user)).status_code, 200)
        self.assertEqual(self.view.call_count, 2)

    def test_admin_and_other_groups_have_no_implicit_crm_bypass(self):
        Group.objects.create(name="CRM_VIEWER").user_set.add(self.customer)
        for user, permission in (
            (self.admin, "CRM_MANAGER"),
            (self.customer, "CRM_MANAGER"),
            (self.service, "CRM_MANAGER"),
            (self.manager, "CUSTOMER_SERVICE"),
        ):
            with self.subTest(permission=permission, user=user.email):
                self.assertEqual(role_required(permission)(self.view)(self.request(user)).status_code, 302)
        self.view.assert_not_called()

    def test_role_input_is_trimmed_case_insensitive_and_accepts_constants(self):
        for permission, user in (
            (" admin ", self.admin), (AccountRole.ADMIN, self.admin),
            (" Customer ", self.customer), (" crm_manager ", self.manager),
            (" customer_service ", self.service),
        ):
            with self.subTest(permission=permission):
                self.assertEqual(role_required(permission)(self.view)(self.request(user)).status_code, 200)

    def test_invalid_or_empty_permission_configuration_raises_value_error(self):
        for permission in ("UNKNOWN", "", "   ", None, 42, ["ADMIN"]):
            with self.subTest(permission=permission), self.assertRaises(ValueError):
                role_required(permission)
        with self.assertRaises(ValueError):
            role_required()
        with self.assertRaises(ValueError):
            role_required("ADMIN", "UNKNOWN")
        self.view.assert_not_called()

    def test_locked_accounts_cannot_run_any_protected_view(self):
        for user, permission in (
            (self.admin, "ADMIN"), (self.customer, "CUSTOMER"),
            (self.manager, "CRM_MANAGER"), (self.service, "CUSTOMER_SERVICE"),
        ):
            with self.subTest(permission=permission):
                user.status = AccountStatus.LOCKED
                user.save(update_fields=["status"])
                self.assertFalse(user.is_active)
                self.assertEqual(role_required(permission)(self.view)(self.request(user)).status_code, 403)
        self.view.assert_not_called()

    def test_lock_in_database_blocks_stale_active_user(self):
        Account.objects.filter(pk=self.manager.pk).update(status=AccountStatus.LOCKED)
        self.assertTrue(self.manager.is_active)
        response = role_required("CRM_MANAGER")(self.view)(self.request(self.manager))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(get_home_path(self.manager), "/")
        self.view.assert_not_called()

    def test_role_revocation_in_database_blocks_stale_admin(self):
        Account.objects.filter(pk=self.admin.pk).update(role=AccountRole.CUSTOMER)
        self.assertEqual(self.admin.role, AccountRole.ADMIN)
        response = role_required("ADMIN")(self.view)(self.request(self.admin))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.view.assert_not_called()

    def test_group_revocation_blocks_prefetched_membership(self):
        cached = Account.objects.prefetch_related("groups").get(pk=self.manager.pk)
        self.manager.groups.remove(self.manager_group)
        response = role_required("CRM_MANAGER")(self.view)(self.request(cached))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")
        self.view.assert_not_called()

    def test_deleted_account_is_forbidden_and_has_safe_home(self):
        cached = Account.objects.get(pk=self.customer.pk)
        Account.objects.filter(pk=cached.pk).delete()
        self.assertEqual(role_required("CUSTOMER")(self.view)(self.request(cached)).status_code, 403)
        self.assertEqual(get_home_path(cached), "/")
        self.view.assert_not_called()

    def test_denied_home_does_not_loop_even_without_trailing_slash(self):
        for user, path in (
            (self.customer, "/"), (self.manager, "/crm/"),
            (self.manager, "/crm"), (self.service, "/crm/"),
            (self.admin, "/admin-portal/"), (self.admin, "/admin-portal"),
        ):
            with self.subTest(user=user.email, path=path):
                request = self.request(user, path + "?page=2")
                response = role_required("CUSTOMER_SERVICE" if user == self.admin else "ADMIN")(self.view)(request)
                self.assertEqual(response.status_code, 403)
                self.assertNotIn("Location", response)
                self.assertIn("Bạn không có quyền truy cập chức năng này.", response.content.decode())
        self.view.assert_not_called()

    def test_home_mapping_and_group_priority_over_customer(self):
        for user, destination in (
            (self.admin, "/admin-portal/"), (self.manager, "/crm/"),
            (self.service, "/crm/"), (self.customer, "/"),
        ):
            with self.subTest(user=user.email):
                self.assertEqual(get_home_path(user), destination)
        self.manager.groups.add(self.service_group)
        self.assertEqual(get_home_path(self.manager), "/crm/")
        self.admin.groups.add(self.manager_group, self.service_group)
        self.assertEqual(get_home_path(self.admin), "/admin-portal/")

    def test_anonymous_unknown_and_inactive_home_fall_back_to_root(self):
        for user in (AnonymousUser(), None, SimpleNamespace(is_authenticated=True)):
            with self.subTest(user=user):
                self.assertEqual(get_home_path(user), "/")
        self.admin.status = AccountStatus.LOCKED
        self.admin.save(update_fields=["status"])
        self.assertEqual(get_home_path(self.admin), "/")

    def test_decorator_preserves_view_metadata_and_passes_arguments(self):
        def protected_view(request, item_id, *, label):
            """Protected view documentation."""
            return HttpResponse(f"{item_id}:{label}")

        wrapped = role_required("ADMIN")(protected_view)
        self.assertEqual(wrapped.__name__, protected_view.__name__)
        self.assertEqual(wrapped.__doc__, protected_view.__doc__)
        self.assertIs(wrapped.__wrapped__, protected_view)
        self.assertEqual(wrapped(self.request(self.admin), 7, label="ok").content, b"7:ok")
