"""Environment-driven configuration constants."""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional; env vars can be set by the shell/container

# Database connection is mandatory when running with USE_DB=1; no
# defaults are provided to avoid accidental credential leakage.
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME")


def require_db_vars():
    """Raise RuntimeError if any required DB env vars are missing.

    Called by get_engine() at connection time, not at import time, so that
    tests running with USE_DB=0 are never affected.
    """
    missing = [
        k for k, v in [
            ("DB_USER", DB_USER),
            ("DB_PASSWORD", DB_PASSWORD),
            ("DB_HOST", DB_HOST),
            ("DB_NAME", DB_NAME),
        ]
        if not v
    ]
    if missing:
        raise RuntimeError(f"missing required DB env vars: {', '.join(missing)}")

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# Cache table name for taste profiles
TASTE_PROFILE_TABLE = "taste_profiles"
