from apps.accounts.testing import PortalTestCase as TestCase, PortalClient as Client


from apps.accounts.models import Account


class CrossPortalCsrfTests(TestCase):
    password = 'StrongPass!2026'

    @classmethod
    def setUpTestData(cls):
        cls.actors = {
            '/admin/login/': Account.objects.create_superuser('csrf-admin@portal.test', cls.password),
            '/manager/login/': Account.objects.create_user('csrf-manager@portal.test', cls.password, role='MANAGER'),
            '/login/': Account.objects.create_user('csrf-customer@portal.test', cls.password),
        }
        cls.cookies = {'/admin/login/': 'staff_sessionid', '/manager/login/': 'manager_sessionid', '/login/': 'sessionid'}
        cls.homes = {'/admin/login/': '/admin/', '/manager/login/': '/manager/', '/login/': '/account/profile/'}

    def browser(self):
        from django.test import Client as BrowserClient
        return BrowserClient(enforce_csrf_checks=True)

    def token(self, response):
        import re
        return re.search(r'name="csrfmiddlewaretoken" value="([A-Za-z0-9]+)"', response.content.decode())[1]

    def sign_in(self, browser, path, token):
        return browser.post(path, {'email': self.actors[path].email, 'password': self.password,
                                   'csrfmiddlewaretoken': token})

    def test_all_six_login_orders_rotate_csrf_and_preserve_sessions_and_logout(self):
        from itertools import permutations
        for order in permutations(self.actors):
            with self.subTest(order=order):
                browser = self.browser()
                for path in order:
                    browser.get(path)
                    old_csrf = browser.cookies['csrftoken'].value
                    sessions = {name: cookie.value for name, cookie in browser.cookies.items() if name in self.cookies.values()}
                    # The capture handler supplies the current shared cookie secret.
                    self.assertEqual(self.sign_in(browser, path, old_csrf).status_code, 302)
                    self.assertNotEqual(browser.cookies['csrftoken'].value, old_csrf)
                    for name, value in sessions.items():
                        self.assertEqual(browser.cookies[name].value, value)
                    self.assertEqual(browser.get(self.homes[path]).wsgi_request.user.pk, self.actors[path].pk)
                for path in order:
                    logout = {'/admin/login/':'/admin/logout/', '/manager/login/':'/manager/logout/', '/login/':'/logout/'}[path]
                    before = {name: browser.cookies[name].value for name in self.cookies.values()}
                    response = browser.post(logout, {'csrfmiddlewaretoken':browser.cookies['csrftoken'].value})
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response.cookies[self.cookies[path]]['max-age'], 0)
                    for other in set(self.cookies.values()) - {self.cookies[path]}:
                        self.assertEqual(browser.cookies[other].value, before[other])

    def test_preopened_stale_forms_get_safe_empty_retry_without_authentication(self):
        from itertools import permutations
        from unittest.mock import patch
        for first, stale in permutations(self.actors, 2):
            with self.subTest(first=first, stale=stale):
                browser = self.browser()
                old_forms = {path:self.token(browser.get(path)) for path in self.actors}
                self.assertEqual(self.sign_in(browser, first, old_forms[first]).status_code, 302)
                first_key = browser.cookies[self.cookies[first]].value
                with patch('apps.admin_portal.views.authenticate') as staff_auth, patch('apps.accounts.customer_forms.authenticate') as customer_auth:
                    rejected = self.sign_in(browser, stale, old_forms[stale])
                    self.assertEqual(rejected.status_code, 403)
                    staff_auth.assert_not_called()
                    customer_auth.assert_not_called()
                self.assertNotContains(rejected, self.password, status_code=403)
                self.assertNotContains(rejected, f'value="{self.actors[stale].email}"', status_code=403)
                self.assertContains(rejected, 'role="alert"', status_code=403)
                self.assertIn('no-store', rejected['Cache-Control'])
                self.assertNotIn(self.cookies[stale], browser.cookies)
                self.assertEqual(browser.cookies[self.cookies[first]].value, first_key)
                self.assertEqual(self.sign_in(browser, stale, self.token(rejected)).status_code, 302)
                self.assertEqual(browser.cookies[self.cookies[first]].value, first_key)

    def test_missing_forged_tokens_cookie_and_foreign_origin_remain_forbidden(self):
        for path in self.actors:
            for mode in ('missing_token', 'forged_token', 'missing_cookie', 'origin', 'referer'):
                with self.subTest(path=path, mode=mode):
                    browser = self.browser()
                    token = self.token(browser.get(path))
                    data = {'email': self.actors[path].email, 'password': self.password, 'csrfmiddlewaretoken':token}
                    kwargs = {}
                    if mode == 'missing_token': data.pop('csrfmiddlewaretoken')
                    if mode == 'forged_token': data['csrfmiddlewaretoken'] = 'A' * 32
                    if mode == 'missing_cookie': browser.cookies.clear()
                    if mode == 'origin': kwargs['HTTP_ORIGIN'] = 'https://attacker.example'
                    if mode == 'referer': kwargs.update(secure=True, HTTP_REFERER='https://attacker.example/')
                    response = browser.post(path, data, **kwargs)
                    self.assertEqual(response.status_code, 403)
                    self.assertFalse(any(name in browser.cookies for name in self.cookies.values()))
                    self.assertNotContains(response, self.password, status_code=403)

    def test_stale_logout_is_not_replayed_and_other_portals_remain_authenticated(self):
        browser = self.browser()
        stale = self.token(browser.get('/admin/login/'))
        self.assertEqual(self.sign_in(browser, '/admin/login/', stale).status_code, 302)
        self.assertEqual(self.sign_in(browser, '/manager/login/', browser.cookies['csrftoken'].value).status_code, 302)
        keys = {name:browser.cookies[name].value for name in ('staff_sessionid','manager_sessionid')}
        self.assertEqual(browser.post('/admin/logout/', {'csrfmiddlewaretoken':stale}).status_code, 403)
        for name,value in keys.items(): self.assertEqual(browser.cookies[name].value, value)
        self.assertEqual(browser.post('/admin/logout/', {'csrfmiddlewaretoken':browser.cookies['csrftoken'].value}).status_code, 302)
        self.assertEqual(browser.get('/manager/').wsgi_request.user.pk, self.actors['/manager/login/'].pk)

    def test_httponly_cookie_stale_form_can_retry_with_fresh_rendered_token(self):
        from django.test import override_settings
        with override_settings(CSRF_COOKIE_HTTPONLY=True):
            browser = self.browser()
            stale = self.token(browser.get('/manager/login/'))
            self.assertEqual(self.sign_in(browser, '/admin/login/', browser.cookies['csrftoken'].value).status_code, 302)
            response = self.sign_in(browser, '/manager/login/', stale)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(self.sign_in(browser, '/manager/login/', self.token(response)).status_code, 302)


class PortalSessionTests(TestCase):
    def test_unified_login_selects_role_cookie_without_overwriting_other_portals(self):
        from django.test import Client as BrowserClient
        password = 'StrongPass!2026'
        actors = [Account.objects.create_user('unified-customer@test.example', password),
                  Account.objects.create_superuser('unified-admin@test.example', password),
                  Account.objects.create_user('unified-manager@test.example', password, role='MANAGER')]
        browser = BrowserClient()
        for actor, cookie, destination in zip(actors, ['sessionid', 'staff_sessionid', 'manager_sessionid'], ['/', '/admin/', '/manager/']):
            with self.subTest(role=actor.role):
                existing = {name: value.value for name, value in browser.cookies.items() if name.endswith('sessionid')}
                response = browser.post('/login/', {'email': actor.email, 'password': password})
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, destination)
                self.assertIn(cookie, response.cookies)
                for name, key in existing.items():
                    self.assertEqual(browser.cookies[name].value, key)
                self.assertEqual(browser.get(destination).wsgi_request.user.pk, actor.pk)
        self.assertEqual(browser.get('/account/password/change/').wsgi_request.user.pk, actors[0].pk)
        self.assertEqual(browser.get('/account/password/change/?portal=manager').wsgi_request.user.pk, actors[2].pk)

    def test_manager_logout_without_customer_cookie_retains_admin_shared_crm(self):
        from django.test import Client as BrowserClient
        password = 'StrongPass!2026'
        admin = Account.objects.create_superuser('fallback-admin@test.example', password)
        manager = Account.objects.create_user('fallback-manager@test.example', password, role='MANAGER')
        browser = BrowserClient()
        for actor in (admin, manager):
            browser.post('/login/', {'email': actor.email, 'password': password})
        admin_key = browser.cookies['staff_sessionid'].value
        response = browser.post('/manager/logout/')
        self.assertEqual(response.cookies['manager_sessionid']['max-age'], 0)
        self.assertEqual(browser.cookies['staff_sessionid'].value, admin_key)
        self.assertEqual(browser.get('/crm/customers/').wsgi_request.user.pk, admin.pk)
        self.assertFalse(browser.get('/manager/').wsgi_request.user.is_authenticated)

    def test_expired_revoked_locked_and_changed_role_manager_cannot_mask_valid_admin(self):
        from django.test import Client as BrowserClient
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        from datetime import timedelta
        password = 'StrongPass!2026'
        admin = Account.objects.create_superuser('state-admin@test.example', password)
        manager = Account.objects.create_user('state-manager@test.example', password, role='MANAGER')
        for state in ('expired', 'password', 'locked', 'role'):
            with self.subTest(state=state):
                manager.set_password(password); manager.status='ACTIVE'; manager.role='MANAGER'; manager.save()
                browser = BrowserClient()
                for actor in (admin,manager):
                    browser.post('/login/', {'email': actor.email, 'password': password})
                if state == 'expired':
                    Session.objects.filter(session_key=browser.cookies['manager_sessionid'].value).update(expire_date=timezone.now()-timedelta(seconds=1))
                elif state == 'password':
                    manager.set_password(password+'Changed'); manager.save()
                elif state == 'locked':
                    Account.objects.filter(pk=manager.pk).update(status='LOCKED')
                else:
                    Account.objects.filter(pk=manager.pk).update(role='CUSTOMER')
                self.assertEqual(browser.get('/crm/customers/').wsgi_request.user.pk, admin.pk)
                denied = browser.get('/manager/')
                self.assertIn(denied.status_code, (302,403))

    def test_admin_manager_customer_sessions_and_logout_are_independent(self):
        password = 'StrongPass!2026'
        admin = Account.objects.create_superuser('admin@parallel.test', password)
        manager = Account.objects.create_user('manager@parallel.test', password, role='MANAGER')
        customer = Account.objects.create_user('customer@parallel.test', password)
        client = Client()
        for path, account in [('/login/', customer), ('/admin/login/', admin), ('/manager/login/', manager)]:
            self.assertEqual(client.post(path, {'email': account.email, 'password': password}).status_code, 302)
        for path, account in [('/', customer), ('/admin/', admin), ('/manager/', manager), ('/crm/', manager)]:
            self.assertEqual(client.get(path).wsgi_request.user.pk, account.pk)
        client.post('/admin/logout/')
        self.assertEqual(client.get('/manager/').wsgi_request.user.pk, manager.pk)
        self.assertEqual(client.get('/').wsgi_request.user.pk, customer.pk)
        client.post('/admin/login/', {'email': admin.email, 'password': password})
        client.post('/manager/logout/')
        self.assertEqual(client.get('/admin/').wsgi_request.user.pk, admin.pk)
        self.assertEqual(client.get('/').wsgi_request.user.pk, customer.pk)
        self.assertFalse(client.get('/manager/').wsgi_request.user.is_authenticated)

    def test_staff_and_customer_login_and_logout_are_independent(self):
        password = 'StrongPass!2026'
        admin = Account.objects.create_superuser('admin@session.test', password)
        customer = Account.objects.create_user('customer@session.test', password)
        client = Client()
        client.post('/login/', {'email': customer.email, 'password': password})
        customer_key = client.cookies['sessionid'].value
        response = client.post('/admin/login/', {'email': admin.email, 'password': password})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.cookies['sessionid'].value, customer_key)
        self.assertEqual(client.get('/').wsgi_request.user.pk, customer.pk)
        self.assertEqual(client.get('/admin/').wsgi_request.user.pk, admin.pk)
        client.post('/admin/logout/')
        self.assertEqual(client.get('/').wsgi_request.user.pk, customer.pk)
        self.assertFalse(client.get('/admin/').wsgi_request.user.is_authenticated)
        client.post('/admin/login/', {'email': admin.email, 'password': password})
        client.post('/logout/')
        self.assertFalse(client.get('/').wsgi_request.user.is_authenticated)
        self.assertEqual(client.get('/admin/').wsgi_request.user.pk, admin.pk)
