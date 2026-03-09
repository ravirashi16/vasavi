"""Environment-driven configuration constants."""

import os

DB_USER = os.environ.get("DB_USER", "dev")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Tartan#20222")
DB_HOST = os.environ.get("DB_HOST", "10.111.5.172")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "dev_reczdb")

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# Cache table name for taste profiles
TASTE_PROFILE_TABLE = "taste_profiles"
