from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm_mode"] in ("mock", "replay")


def test_default_llm_mode_is_mock() -> None:
    assert settings.LLM_MODE == "mock"


def test_live_requires_ack() -> None:
    s = settings.model_copy(update={"LLM_MODE": "live", "LLM_LIVE_ACK": "no"})
    import pytest

    with pytest.raises(RuntimeError):
        s.assert_live_allowed()
