"""Settings shared by every environment.

Anything environment-specific lives in ``dev.py`` / ``prod.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# repository root — the already-verified static frontend lives here.
ROOT_DIR = BASE_DIR.parent

# Read backend/.env first, then the process environment wins over it so that
# real deployment variables can override anything written in the file.
load_dotenv(BASE_DIR / ".env", override=False)

from config.db import database_config  # noqa: E402  (needs BASE_DIR + dotenv)

# ---------------------------------------------------------------- core -----

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "insecure-dev-only-key-do-not-use-in-production",
)

DEBUG = False

ALLOWED_HOSTS: list[str] = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INTERNAL_IPS = ["127.0.0.1"]

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # GreenShop
    "core.apps.CoreConfig",
    "catalog.apps.CatalogConfig",
    "orders.apps.OrdersConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise sits directly after SecurityMiddleware, as documented.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.shop",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = database_config()

# ------------------------------------------------------------ auth --------

AUTH_USER_MODEL = "core.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "core:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

# --------------------------------------------------------- i18n / tz ------

LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------- static / media ---

STATIC_URL = "/static/"
# The verified frontend (style.css, the five mobile layers, main.js, images)
# was copied in from the repository root so that `backend/` is self-contained
# and can be shipped to a VPS on its own.
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------- shop -------

SITE_NAME = "GreenShop"
CURRENCY = "$"
# Products per page in the catalogue grid.
PRODUCTS_PER_PAGE = int(os.environ.get("PRODUCTS_PER_PAGE", "9"))
REVIEWS_PER_PAGE = int(os.environ.get("REVIEWS_PER_PAGE", "5"))
# Anonymous carts live this long before they are collected.
CART_SESSION_DAYS = int(os.environ.get("CART_SESSION_DAYS", "30"))

# -------------------------------------------------------------- misc ------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB — product photos
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Sessions are the cart key for anonymous visitors.
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * CART_SESSION_DAYS

# Logging that surfaces the SQLite fallback and admin actions during dev.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"level": "INFO", "propagate": True},
        "catalog": {"level": "DEBUG", "propagate": True},
        "orders": {"level": "DEBUG", "propagate": True},
    },
}
