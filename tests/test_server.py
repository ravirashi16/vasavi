from fastapi.testclient import TestClient
from vasuvi.server import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json().get("status") == "ok"


def test_profile_endpoint(monkeypatch):
    # patch the name as bound in server.py, not in core
    import vasuvi.server as server_mod
    monkeypatch.setattr(server_mod, "get_user_taste_profile", lambda u, as_of=None: {"taste_profile": {"dummy": "value"}})
    res = client.get("/users/1/profile")
    assert res.status_code == 200
    assert res.json()["taste_profile"]["dummy"] == "value"
