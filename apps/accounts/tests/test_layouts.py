from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.staticfiles import finders
from django.template import engines
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.urls import Resolver404, resolve


class SharedLayoutTests(SimpleTestCase):
    templates = ("layouts/base_customer.html", "layouts/base_crm.html")

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
                     'Trang chủ', 'Sản phẩm', 'Khảo sát của tôi', 'Tài khoản'):
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

    def test_shared_foundation_does_not_register_shop_or_crm_home(self):
        for path in ('/', '/crm/'):
            with self.subTest(path=path), self.assertRaises(Resolver404):
                resolve(path)
