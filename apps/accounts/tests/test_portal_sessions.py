from apps.accounts.testing import PortalTestCase as TestCase, PortalClient as Client


from apps.accounts.models import Account


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
