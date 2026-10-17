from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.staticfiles import finders
from django.template import engines
from django.template.loader import get_template, render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import resolve


class SharedLayoutTests(SimpleTestCase):
    templates = ("layouts/base_customer.html", "layouts/base_crm.html")

    def setUp(self):
        # These tests cover layout contracts without querying business data.
        # Category navigation is exercised against the test database by shop tests.
        navigation = patch("apps.shop.templatetags.shop_ui.active_shop_categories", return_value=[])
        navigation.start()
        self.addCleanup(navigation.stop)

    def request(self, user=None):
        request = RequestFactory().get("/")
        request.user = user if user is not None else AnonymousUser()
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_customer_layout_renders_for_anonymous_without_missing_urls(self):
        html = render_to_string(self.templates[0], request=self.request())
        for text in ('<!doctype html>', 'lang="vi"', 'name="viewport"',
                     '/static/css/customer.css', '<header', '<footer',
                     'Trang chủ', 'Sản phẩm', 'Tìm tên sản phẩm', 'Tài khoản'):
            self.assertIn(text, html)
        self.assertNotIn('customer-user', html)
        self.assertNotIn('admin_portal.css', html)
        self.assertNotIn('portal-sidebar', html)

    def test_crm_layout_renders_for_anonymous_without_missing_urls(self):
        html = render_to_string(self.templates[1], request=self.request())
        for text in ('<!doctype html>', 'lang="vi"', 'name="viewport"',
                     '/static/css/crm.css', '<aside', '<nav',
                     'Tổng quan', 'Khách hàng', 'Phản hồi', 'Khảo sát'):
            self.assertIn(text, html)
        self.assertNotIn('crm-user', html)
        self.assertNotIn('admin_portal.css', html)
        self.assertNotIn('portal-sidebar', html)
        self.assertNotIn('/static/css/customer.css', html)

    def test_authenticated_email_and_messages_render_and_escape_content(self):
        user = SimpleNamespace(is_authenticated=True, email='<script>alert("email")</script>')
        for name in self.templates:
            with self.subTest(template=name):
                request = self.request(user)
                messages.success(request, "Thao tác thành công.")
                messages.error(request, '<script>alert("message")</script>')
                html = render_to_string(name, request=request)
                self.assertIn('Thao tác thành công.', html)
                self.assertIn('aria-live="polite"', html)
                self.assertIn('&lt;script&gt;alert(&quot;email&quot;)&lt;/script&gt;', html)
                self.assertIn('&lt;script&gt;alert(&quot;message&quot;)&lt;/script&gt;', html)
                self.assertNotIn('<script>alert(', html)

    def test_customer_child_can_override_all_shared_blocks(self):
        template = engines['django'].from_string('''
            {% extends "layouts/base_customer.html" %}
            {% block title %}Customer test title{% endblock %}
            {% block extra_css %}<link href="/child.css" rel="stylesheet">{% endblock %}
            {% block content %}<h1>Customer test content</h1>{% endblock %}
            {% block extra_js %}<script src="/child.js"></script>{% endblock %}
        ''')
        html = template.render({}, request=self.request())
        for text in ('Customer test title', '/child.css', 'Customer test content', '/child.js'):
            self.assertIn(text, html)

    def test_crm_child_can_override_all_shared_blocks(self):
        template = engines['django'].from_string('''
            {% extends "layouts/base_crm.html" %}
            {% block title %}CRM test title{% endblock %}
            {% block page_title %}CRM test heading{% endblock %}
            {% block extra_css %}<link href="/child.css" rel="stylesheet">{% endblock %}
            {% block content %}<p>CRM test content</p>{% endblock %}
            {% block extra_js %}<script src="/child.js"></script>{% endblock %}
        ''')
        html = template.render({}, request=self.request())
        for text in ('CRM test title', 'CRM test heading', '/child.css', 'CRM test content', '/child.js'):
            self.assertIn(text, html)

    def test_layout_static_assets_are_available(self):
        self.assertTrue(finders.find('css/customer.css'))
        self.assertTrue(finders.find('css/crm.css'))

    def test_tv1_registers_shop_and_crm_home_without_admin_route_changes(self):
        self.assertEqual(resolve('/').view_name, 'shop:home')
        self.assertEqual(resolve('/admin/login/').view_name, 'admin_login')
        self.assertEqual(resolve('/manager/login/').view_name, 'manager_login')


class PortalTemplateResolutionTests(SimpleTestCase):
    def test_custom_portal_templates_resolve_from_the_portal_subdirectory(self):
        for relative_name in ("base.html", "database.html", "login.html",
                              "partials/messages.html", "partials/sidebar.html"):
            with self.subTest(template=relative_name):
                template = get_template(f"admin/portal/{relative_name}")
                expected = Path(settings.BASE_DIR) / "templates" / "admin" / "portal" / relative_name
                self.assertEqual(Path(template.origin.name).resolve(), expected.resolve())

    def test_django_admin_templates_resolve_from_the_framework(self):
        framework_templates = Path(apps.get_app_config("admin").path) / "templates"
        for name in ("base.html", "base_site.html", "login.html", "index.html"):
            with self.subTest(template=name):
                template = get_template(f"admin/{name}")
                self.assertEqual(Path(template.origin.name).resolve(),
                                 (framework_templates / "admin" / name).resolve())

    def test_shared_staff_login_and_manager_alias_render_one_independent_login_page(self):
        from apps.admin_portal.views import PortalLoginForm

        for name in ("admin/portal/login.html", "manager/login.html"):
            with self.subTest(template=name):
                request = RequestFactory().get("/admin/login/")
                request.user = AnonymousUser()
                html = render_to_string(name, {"form": PortalLoginForm(), "next": ""}, request=request)
                self.assertEqual(html.lower().count("<!doctype html>"), 1)
                self.assertIn("CRM STAFF PORTAL", html)
                self.assertIn('name="email"', html)
                self.assertIn('name="password"', html)
                self.assertIn('name="csrfmiddlewaretoken"', html)
                self.assertNotIn('id="site-name"', html)


class RoleLayoutIntegrationTests(TestCase):
    def test_manager_crm_and_catalog_urls_keep_manager_shell_and_active_navigation(self):
        from apps.accounts.models import Account

        manager = Account.objects.create_user("manager-layout@example.test", "StrongPass!2026", role="MANAGER")
        self.client.force_login(manager)
        for url, active_label in (("/crm/customers/", "Customers"), ("/manager/catalog/products/", "Products")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "CRM MANAGER PORTAL")
                self.assertContains(response, f'>{active_label}</a>')
                self.assertNotContains(response, "CRM ADMIN PORTAL")
                self.assertNotContains(response, "Database Tools")
                self.assertContains(response, "/static/css/admin_portal.css")

    def test_admin_crm_url_keeps_admin_shell(self):
        from apps.accounts.models import Account

        admin = Account.objects.create_superuser("admin-layout@example.test", "StrongPass!2026")
        self.client.force_login(admin)
        response = self.client.get("/crm/customers/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CRM ADMIN PORTAL")
        self.assertContains(response, "Database Tools")
        self.assertNotContains(response, "CRM MANAGER PORTAL")
