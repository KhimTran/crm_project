"""Run migrations/tests only on the dedicated TV1 MySQL database."""
from .settings import *  # noqa: F403

DATABASES['default']['TEST'] = {
    'NAME': 'test_crm_db',
    'CHARSET': 'utf8mb4',
    'COLLATION': 'utf8mb4_unicode_ci',
}
CONTENT_AUTO_TRANSLATE = False  # tv4: test không gọi dịch vụ dịch qua mạng và không ghi file bản dịch
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
