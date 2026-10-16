"""Settings dispatcher.

``manage.py``, ``wsgi.py`` and ``asgi.py`` all point at ``config.settings``.
Which concrete settings module gets loaded is decided by ``DJANGO_ENV``:

    DJANGO_ENV=dev   (default) -> config.settings.dev
    DJANGO_ENV=prod            -> config.settings.prod
"""

import os

_env = os.environ.get("DJANGO_ENV", "dev").strip().lower()

if _env == "prod":
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403
