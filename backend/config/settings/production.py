"""
AIU — Production Settings
Compatible with: Render (free + paid), Railway, Heroku, VPS
"""

from .base import *  # noqa: F401, F403
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

# ── ALLOWED_HOSTS — accept cloud platform auto-domains ───────────────────────
_extra_hosts = [
    ".onrender.com",
    ".railway.app",
    ".up.railway.app",
    ".herokuapp.com",
]
ALLOWED_HOSTS = ALLOWED_HOSTS + _extra_hosts  # noqa: F405

# ── SSL — handled by Render/Railway edge proxy, NOT by Django ─────────────────
# IMPORTANT: Do NOT set SECURE_SSL_REDIRECT=True on Render free tier.
# Render's health checker hits http:// internally — SSL redirect breaks it.
# Render/Railway terminate SSL at their load balancer and forward plain HTTP.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Set connection max age to 0 for Render free (avoids stale connection errors)
DATABASES = {
    "default": {
        **DATABASES["default"],  # noqa: F405
        "CONN_MAX_AGE": 0,
    }
}

# Security headers (safe to keep — don't break anything)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# ── Static files — WhiteNoise serves them (already in base.py) ───────────────
# WhiteNoiseMiddleware is in MIDDLEWARE in base.py
# STATICFILES_STORAGE = CompressedManifestStaticFilesStorage in base.py
# collectstatic runs in the Dockerfile CMD (start command), not at build time

# ── File Storage ──────────────────────────────────────────────────────────────
# Using local storage by default — works on Render free tier
# For production with uploads, set these env vars and uncomment:
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
# AWS_ACCESS_KEY_ID     = env("AWS_ACCESS_KEY_ID", default="")
# AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
# AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
# AWS_S3_REGION_NAME    = env("AWS_S3_REGION_NAME", default="us-east-1")

# ── Sentry error tracking (optional — works without it) ───────────────────────
_sentry_dsn = os.environ.get("SENTRY_DSN", "")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[
            DjangoIntegration(transaction_style="url"),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production",
    )
   
   
   
   
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
    "https://*.vercel.app",
]
# CSRF_TRUSTED_ORIGINS = [
#     "https://*.onrender.com",
#     "https://your-frontend.vercel.app",
# ]