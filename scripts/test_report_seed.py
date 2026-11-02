"""Run legacy report fixtures, which authenticate via Django's default test cookie."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.test import override_settings
from django.core.management import call_command
middleware = [item.replace('apps.accounts.middleware.PortalSessionMiddleware',
                           'django.contrib.sessions.middleware.SessionMiddleware')
              for item in settings.MIDDLEWARE]
with override_settings(MIDDLEWARE=middleware):
    call_command('test', 'apps.customers.tests.test_favorite_brand',
                 'apps.customers.tests.test_customer_report',
                 'apps.surveys.test_survey_report', 'apps.surveys.test_questionnaire',
                 interactive=False)
