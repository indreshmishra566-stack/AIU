"""
AIU — Development Settings
"""

from importlib.util import find_spec

from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Use console email in dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django Debug Toolbar
if find_spec("debug_toolbar"):
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# Relaxed CORS for local frontend dev
CORS_ALLOW_ALL_ORIGINS = True

# Task always eager so no Redis needed for quick dev
CELERY_TASK_ALWAYS_EAGER = False  # set True to skip broker locally

LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
