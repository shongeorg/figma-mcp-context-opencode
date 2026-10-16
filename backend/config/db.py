"""Database resolution.

The project is pointed at a **Neon** Postgres instance through the single
``NEON_DB`` environment variable, which holds a full DSN::

    NEON_DB=postgresql://user:password@ep-xyz.aws.neon.tech/neondb?sslmode=require

Neon terminates TLS on the public endpoint, so ``sslmode`` defaults to
``require`` when the DSN does not spell it out, and pooled connections are
kept alive for a while because every request would otherwise pay a fresh
TLS handshake against a server in another region.

When ``NEON_DB`` is absent the project falls back to a local SQLite file so
that ``manage.py migrate`` / ``runserver`` work straight after ``git clone``.
That fallback prints a loud warning: it is a convenience, not a target.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

BASE_DIR = Path(__file__).resolve().parent.parent

SQLITE_FALLBACK = BASE_DIR / "db.sqlite3"


def _dsn_to_django(dsn: str) -> dict:
    """Turn a Postgres DSN into a Django ``DATABASES["default"]`` entry.

    Django's PostgreSQL backend only forwards ``OPTIONS`` (plus HOST/PORT/
    USER/PASSWORD) to psycopg — everything else in the DSN query string is
    silently dropped. The query parameters are therefore copied wholesale
    into ``OPTIONS``; otherwise ``sslmode=require`` never reaches the driver
    and Neon refuses the connection as insecure.
    """
    parts = urlsplit(dsn.strip())

    if parts.scheme not in {"postgres", "postgresql"}:
        raise ValueError(
            "NEON_DB must be a postgres:// or postgresql:// DSN, "
            f"got scheme {parts.scheme!r}"
        )

    # Neon terminates TLS on the public endpoint; be explicit if the DSN
    # does not spell it out.
    query = dict(parse_qsl(parts.query))
    query.setdefault("sslmode", "require")

    name = unquote(parts.path.lstrip("/")) or "neondb"
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": unquote(parts.username or ""),
        "PASSWORD": unquote(parts.password or ""),
        "HOST": parts.hostname or "",
        "PORT": str(parts.port or ""),
        "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "600")),
        "CONN_HEALTH_CHECKS": True,
        "ATOMIC_REQUESTS": True,
        # NOTE: no statement_timeout here on purpose. Neon's pooler endpoint
        # rejects unknown startup parameters with "unsupported startup
        # parameter in options: statement_timeout".
        "OPTIONS": query,
    }


def database_config() -> dict:
    """Return the ``DATABASES`` mapping for the current environment."""
    dsn = os.environ.get("NEON_DB", "").strip()

    if dsn:
        return {"default": _dsn_to_django(dsn)}

    sys.stderr.write(
        "\n"
        "  !! NEON_DB is not set — falling back to local SQLite.\n"
        f"  !! Data is stored in {SQLITE_FALLBACK}\n"
        "  !! Put your Neon DSN in backend/.env to use Postgres:\n"
        "  !!   NEON_DB=postgresql://user:pass@ep-xyz.aws.neon.tech/neondb\n"
        "\n"
    )
    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": SQLITE_FALLBACK,
            "OPTIONS": {"timeout": 20},
        }
    }
