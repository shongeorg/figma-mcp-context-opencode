"""Production settings — selected with ``DJANGO_ENV=prod``."""

from .base import *  # noqa: F401,F403
from .base import SECRET_KEY  # noqa: F401

DEBUG = False

if SECRET_KEY.startswith("insecure-"):
    raise RuntimeError(
        "DJANGO_SECRET_KEY must be set in production. Generate one with:\n"
        "    python -c \"from django.core.management.utils import "
        "get_random_secret_key; print(get_random_secret_key())\""
    )

# --- security -------------------------------------------------------------

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# --- caching --------------------------------------------------------------

STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # noqa: F405

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "greenshop",
        "TIMEOUT": 60 * 5,
    }
}

# --- e-mail ---------------------------------------------------------------
# Order notifications to the admin are logged to the console until SMTP is
# wired up on the VPS; nothing here talks to a payment provider on purpose.
EMAIL_BACKEND = os.environ.get(  # noqa: F405
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("DJANGO_EMAIL_USE_TLS", "true").lower() == "true"
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL", "shop@greenshop.local")
ORDER_NOTIFY_EMAIL = os.environ.get("ORDER_NOTIFY_EMAIL", DEFAULT_FROM_EMAIL)

# --- logging --------------------------------------------------------------

LOGGING["handlers"]["console"]["level"] = "WARNING"  # noqa: F405
LOGGING["root"]["level"] = "WARNING"  # noqa: F405
