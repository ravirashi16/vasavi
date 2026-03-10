from fastapi.testclient import TestClient
from vasuvi.server import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json().get("status") == "ok"


def test_profile_endpoint(monkeypatch):
    # patch service call to avoid DB/LLM
    from vasuvi import core
    monkeypatch.setattr(core, "get_user_taste_profile", lambda u, as_of=None: {"taste_profile": {"dummy": "value"}})
    res = client.get("/users/1/profile")
    assert res.status_code == 200
    assert res.json()["taste_profile"]["dummy"] == "value"
