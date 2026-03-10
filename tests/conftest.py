import os
import json
import pytest

@pytest.fixture(autouse=True)
def load_env(monkeypatch, tmp_path):
    """Disable DB and wire a temp JSON fixture for every test."""
    # Must patch the module-level booleans directly — setenv alone is too late
    # because USE_DB is evaluated once at import time.
    import vasuvi.db as db_mod
    import vasuvi.processor as proc_mod
    monkeypatch.setenv("USE_DB", "0")
    monkeypatch.setattr(db_mod, "USE_DB", False)
    monkeypatch.setattr(proc_mod, "USE_DB", False)

    # Isolate the JSON profile cache to a temp file so stale cached profiles
    # from previous runs don't short-circuit the LLM mock.
    monkeypatch.setenv("DB_JSON_PATH", str(tmp_path / "taste_profiles.json"))

    fixture = tmp_path / "sample_posts.json"
    with open(fixture, "w") as f:
        json.dump(
            [{"user_id": 1, "post_category_id": 2, "msg": "test",
              "location_name": "", "latitude": 0, "longitude": 0,
              "rating": 5, "created_on": "2024-01-01 00:00:00"}],
            f,
        )
    monkeypatch.setenv("POSTS_JSON", str(fixture))

    # Also patch the module-level cache path constant (evaluated at import time)
    import vasuvi.db as db_mod2
    monkeypatch.setattr(db_mod2, "JSON_CACHE_PATH", str(tmp_path / "taste_profiles.json"))
    return monkeypatch
