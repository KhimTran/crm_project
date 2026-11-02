"""Explicit actor fixtures for routes with independent portal session cookies.

force_login intentionally impersonates one actor across all portals for guard tests.
Real login requests retain the production cookie isolation semantics.
"""
from importlib import import_module
from django.conf import settings
from django.test import Client as DjangoClient, TestCase as DjangoTestCase


class PortalClient(DjangoClient):
    _last_path = '/'
    _forcing = False

    def generic(self, method, path, *args, **kwargs):
        self._last_path = path.split('?',1)[0]
        response = super().generic(method,path,*args,**kwargs)
        selected = getattr(response.wsgi_request, 'portal_session_cookie_name', None)
        self._last_cookie = selected
        if path.split('?',1)[0] == '/login/' and method == 'POST':
            if 'manager_sessionid' in response.cookies:
                self._last_path='/manager/'
            elif 'staff_sessionid' in response.cookies:
                self._last_path='/admin/'
        return response

    @property
    def session(self):
        if self._forcing:
            return DjangoClient.session.fget(self)
        path=self._last_path
        name=getattr(self, '_last_cookie', None) or settings.SESSION_COOKIE_NAME
        if not getattr(self, '_last_cookie', None) and path.startswith('/manager/'):
            name='manager_sessionid'
        elif not getattr(self, '_last_cookie', None) and path.startswith(('/admin/','/django-admin/','/api/')):
            name='staff_sessionid'
        elif not getattr(self, '_last_cookie', None) and path.startswith(('/crm/','/surveys/manage/')):
            name='manager_sessionid' if self.cookies.get('manager_sessionid') else 'staff_sessionid'
        cookie=self.cookies.get(name)
        if cookie:
            return import_module(settings.SESSION_ENGINE).SessionStore(cookie.value)
        return DjangoClient.session.fget(self)

    def force_login(self,user,backend=None):
        self._forcing=True
        try:
            super().force_login(user,backend)
        finally:
            self._forcing=False
        key=self.cookies[settings.SESSION_COOKIE_NAME].value
        for name in ('staff_sessionid','manager_sessionid'):
            self.cookies[name]=key
        self._last_cookie=settings.SESSION_COOKIE_NAME

    def login(self, **credentials):
        self._forcing=True
        try:
            authenticated=super().login(**credentials)
        finally:
            self._forcing=False
        if authenticated:
            key=self.cookies[settings.SESSION_COOKIE_NAME].value
            for name in ('staff_sessionid','manager_sessionid'):
                self.cookies[name]=key
            self._last_cookie=settings.SESSION_COOKIE_NAME
        return authenticated


class PortalTestCase(DjangoTestCase):
    client_class=PortalClient
