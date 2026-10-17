from .base import *  # noqa: F401,F403
from .base import DEBUG, SECRET_KEY

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "0.0.0.0"]

MIDDLEWARE = [m for m in MIDDLEWARE if m != "whitenoise.middleware.WhiteNoiseMiddleware"]  # noqa: F405
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"  # noqa: F405

if SECRET_KEY.startswith("insecure-"):
    import warnings

    warnings.warn(
        "DJANGO_SECRET_KEY is not set — using the development fallback.",
        RuntimeWarning,
        stacklevel=2,
    )
