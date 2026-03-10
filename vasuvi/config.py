"""Environment-driven configuration constants."""

import os

# Database connection is mandatory when running with USE_DB=1; no
# defaults are provided to avoid accidental credential leakage.
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME")

if os.environ.get("USE_DB", "1") == "1":
    missing = [k for k,v in [("DB_USER",DB_USER),("DB_PASSWORD",DB_PASSWORD),("DB_HOST",DB_HOST),("DB_NAME",DB_NAME)] if not v]
    if missing:
        raise RuntimeError(f"missing required DB env vars: {', '.join(missing)}")

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# Cache table name for taste profiles
TASTE_PROFILE_TABLE = "taste_profiles"
