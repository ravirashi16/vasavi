import pytest
from vasuvi import core

class DummyLLM:
    @staticmethod
    def generate_taste_profile_chat(md, key):
        return {"taste_profile": {"tv": "prefers drama"}}

@pytest.fixture(autouse=True)
def patch_llm(monkeypatch):
    import vasuvi.core as core_mod
    monkeypatch.setattr(core_mod, "generate_taste_profile_chat", DummyLLM.generate_taste_profile_chat)


def test_get_user_taste_profile(monkeypatch):
    # ensure some posts exist via fixture
    profile = core.get_user_taste_profile(1)
    assert profile["taste_profile"]["tv"] == "prefers drama"
