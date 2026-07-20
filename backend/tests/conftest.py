"""Session guard: tests must NEVER run in live LLM mode (docs/06 §3)."""

import pytest

from app.config import settings


@pytest.fixture(scope="session", autouse=True)
def forbid_live_llm() -> None:
    assert settings.LLM_MODE != "live", "Tests must not run with LLM_MODE=live (docs/06 §3)"
