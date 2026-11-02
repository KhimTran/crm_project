"""Run migrations/tests only on the dedicated TV1 MySQL database."""
from .settings import *  # noqa: F403
from copy import deepcopy

# Test discovery imports this module even when config.settings is active.
# Never mutate that module's nested connection dictionary through a shared alias.
DATABASES = deepcopy(DATABASES)

DATABASES['default'].setdefault('TEST', {}).update({
    'NAME': 'test_crm_db',
    'CHARSET': 'utf8mb4',
    'COLLATION': 'utf8mb4_unicode_ci',
    'MIRROR': None,
})
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
