from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit

BASE_DIR = Path(__file__).resolve().parent.parent

SQLITE_FALLBACK = BASE_DIR / "db.sqlite3"


def _dsn_to_django(dsn: str) -> dict:
    parts = urlsplit(dsn.strip())

    if parts.scheme not in {"postgres", "postgresql"}:
        raise ValueError(
            "NEON_DB must be a postgres:// or postgresql:// DSN, "
            f"got scheme {parts.scheme!r}"
        )

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
        "OPTIONS": query,
    }


def database_config() -> dict:
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
