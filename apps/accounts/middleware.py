"""Keep staff portal authentication separate from storefront authentication."""
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
import re
from importlib import import_module
from types import SimpleNamespace
from django.contrib.auth import get_user


def select_login_session(request, account):
    name = 'staff_sessionid' if account.role == 'ADMIN' else 'manager_sessionid' if account.role == 'MANAGER' else settings.SESSION_COOKIE_NAME
    current = getattr(request, 'portal_session_cookie_name', settings.SESSION_COOKIE_NAME)
    if name != current:
        request.session = import_module(settings.SESSION_ENGINE).SessionStore(request.COOKIES.get(name))
    request.portal_session_cookie_name = name
    request.staff_session = name != settings.SESSION_COOKIE_NAME


class PortalSessionMiddleware(SessionMiddleware):
    staff_cookie_name = 'staff_sessionid'
    manager_cookie_name = 'manager_sessionid'

    def process_request(self, request):
        path = request.path_info
        if path == '/account/password/change/':
            engine = import_module(settings.SESSION_ENGINE)
            root = engine.SessionStore(request.COOKIES.get(settings.SESSION_COOKIE_NAME))
            root_user = get_user(SimpleNamespace(session=root))
            portal = request.GET.get('portal')
            name = {'manager': self.manager_cookie_name, 'admin': self.staff_cookie_name}.get(portal)
            if name is None and not (root_user.is_authenticated and root_user.role == 'CUSTOMER'):
                for candidate in (self.manager_cookie_name, self.staff_cookie_name):
                    store = engine.SessionStore(request.COOKIES.get(candidate))
                    user = get_user(SimpleNamespace(session=store))
                    if user.is_authenticated and user.role in ('ADMIN', 'MANAGER'):
                        name = candidate
                        break
            request.portal_session_cookie_name = name or settings.SESSION_COOKIE_NAME
            request.staff_session = name is not None
            request.session = engine.SessionStore(request.COOKIES.get(name)) if name else root
            return
        survey_staff_action = bool(re.fullmatch(r'/surveys/\d+/(send|send-result)/', path))
        request.staff_session = (
            path.startswith(('/admin/', '/manager/', '/django-admin/', '/crm/', '/api/'))
            or path.startswith('/surveys/manage/')
            or survey_staff_action
        )
        if not request.staff_session:
            request.portal_session_cookie_name = settings.SESSION_COOKIE_NAME
            return super().process_request(request)
        request.portal_session_cookie_name = self.staff_cookie_name
        if path.startswith('/manager/'):
            request.portal_session_cookie_name = self.manager_cookie_name
        elif path.startswith(('/crm/', '/surveys/manage/')) or survey_staff_action:
            # Shared CRM navigation uses Manager when available, otherwise Admin.
            manager_key = request.COOKIES.get(self.manager_cookie_name)
            manager_store = import_module(settings.SESSION_ENGINE).SessionStore(manager_key) if manager_key else None
            manager_user = get_user(SimpleNamespace(session=manager_store)) if manager_store is not None else None
            valid_manager = manager_user is not None and manager_user.is_authenticated and (
                manager_user.role in ('ADMIN', 'MANAGER') or manager_user.groups.filter(name__in=('CRM_MANAGER','CUSTOMER_SERVICE')).exists())
            if valid_manager:
                request.portal_session_cookie_name = self.manager_cookie_name
        # Select the staff cookie without changing global Django settings.
        engine = import_module(settings.SESSION_ENGINE)
        request.session = engine.SessionStore(request.COOKIES.get(request.portal_session_cookie_name))

    def process_response(self, request, response):
        default = settings.SESSION_COOKIE_NAME
        name = getattr(request, 'portal_session_cookie_name', default)
        previous = request.COOKIES.get(default)
        if name != default:
            if name in request.COOKIES:
                request.COOKIES[default] = request.COOKIES[name]
            else:
                request.COOKIES.pop(default, None)
        try:
            response = super().process_response(request, response)
        finally:
            if previous is not None:
                request.COOKIES[default] = previous
            else:
                request.COOKIES.pop(default, None)
        if getattr(request, 'staff_session', False):
            cookie = response.cookies.pop(settings.SESSION_COOKIE_NAME, None)
            if cookie is not None:
                name = request.portal_session_cookie_name
                response.cookies[name] = cookie.value
                for key, value in cookie.items():
                    response.cookies[name][key] = value
        return response
