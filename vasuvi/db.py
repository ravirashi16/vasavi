"""Cache helpers backed by JSON/CSV file."""

from datetime import date
from typing import Optional, Dict, Any
import json
import os

import pandas as pd

# use database by default; set USE_DB=0 to run in file‑based dev mode
USE_DB = os.environ.get("USE_DB", "1") == "1"

JSON_CACHE_PATH = os.environ.get("DB_JSON_PATH", "taste_profiles.json")  # used only when USE_DB is false

if USE_DB:
    DB_USER = os.environ.get("DB_USER", "dev")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "Tartan#20222")
    DB_HOST = os.environ.get("DB_HOST", "10.111.5.172")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "dev_reczdb")

    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine

    _engine: Optional[Engine] = None

    def get_engine() -> Engine:
        """Return a singleton SQLAlchemy engine configured via env vars."""
        global _engine
        if _engine is None:
            conn = (
                f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )
            _engine = create_engine(conn, pool_pre_ping=True)
        return _engine

    def ensure_table(engine: Engine):
        """Create the taste_profiles table if it doesn't exist."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS taste_profiles (
            user_id BIGINT NOT NULL,
            profile_date DATE NOT NULL,
            payload JSON NOT NULL,
            created_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, profile_date)
        ) ENGINE=InnoDB;
        """
        with engine.begin() as conn:
            conn.execute(text(create_sql))
else:
    def get_engine():
        raise RuntimeError("database support is disabled")

    def ensure_table(engine):
        pass



def _read_cache() -> list[Dict[str, Any]]:
    """Return the list of cached profiles, creating file if missing."""
    if os.path.exists(JSON_CACHE_PATH):
        try:
            with open(JSON_CACHE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _write_cache(data: list[Dict[str, Any]]):
    """Persist the cache list to the JSON path."""
    with open(JSON_CACHE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_cached_profile(user_id: int, as_of: date) -> Optional[Dict[str, Any]]:
    """Retrieve the profile for ``user_id`` on ``as_of`` if present.

    Branches on ``USE_DB``; when true a database query is executed.  The
    JSON file is only consulted when the flag is false.
    """
    if USE_DB:
        engine = get_engine()
        ensure_table(engine)
        query = text(
            "SELECT payload FROM taste_profiles"
            " WHERE user_id = :uid AND profile_date = :pd"
        )
        with engine.connect() as conn:
            result = conn.execute(query, {"uid": user_id, "pd": as_of})
            row = result.fetchone()
            if row:
                return row[0]
        return None

    key = as_of.isoformat()
    for row in _read_cache():
        if row.get("user_id") == user_id and row.get("profile_date") == key:
            return row.get("payload")
    return None


def store_profile(user_id: int, as_of: date, profile: Dict[str, Any]):
    """Write or overwrite a profile in the cache.

    If ``USE_DB`` is true this will perform an upsert into MySQL; otherwise
    it will manipulate the JSON file.  The formats of the two backends are
    equivalent from the caller's perspective.
    """
    if USE_DB:
        engine = get_engine()
        ensure_table(engine)
        upsert = text(
            "INSERT INTO taste_profiles (user_id, profile_date, payload)"
            " VALUES (:uid, :pd, :pl)"
            " ON DUPLICATE KEY UPDATE payload = VALUES(payload)"
        )
        with engine.begin() as conn:
            conn.execute(upsert, {"uid": user_id, "pd": as_of, "pl": json.dumps(profile)})
        return

    # JSON fallback
    key = as_of.isoformat()
    data = _read_cache()
    data = [r for r in data if not (r.get("user_id") == user_id and r.get("profile_date") == key)]
    data.append({"user_id": user_id, "profile_date": key, "payload": profile})
    _write_cache(data)

