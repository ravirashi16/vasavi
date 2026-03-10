import os
import json
import pytest
from vasuvi import config

from vasuvi import db

@pytest.fixture(autouse=True)
def load_env(monkeypatch, tmp_path):
    """Load environment variables for tests and configure a temp DB if needed."""
    # ensure tests don't accidentally hit real database; use sqlite in memory
    monkeypatch.setenv("USE_DB", "0")
    # provide a dummy posts JSON fixture path
    fixture = tmp_path / "sample_posts.json"
    with open(fixture, "w") as f:
        json.dump([{"user_id": 1, "post_category_id": 2, "msg": "test", "location_name": "", "latitude": 0, "longitude": 0, "rating": 5, "created_on": "2024-01-01 00:00:00"}], f)
    monkeypatch.setenv("POSTS_JSON", str(fixture))
    return monkeypatch
