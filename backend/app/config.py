from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central config. See .env.example. LLM policy: docs/06 §3."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: Literal["dev", "test", "prod"] = "dev"

    # LLM policy — mock is the default everywhere (docs/06 §3)
    LLM_MODE: Literal["mock", "replay", "live"] = "mock"
    EMBED_MODE: str = ""  # empty → follows LLM_MODE
    GEMINI_API_KEY: str = ""
    LLM_LIVE_ACK: str = "no"
    LLM_DAILY_BUDGET_USD: float = 2.0

    DATABASE_URL: str = "postgresql+psycopg://kavach:kavach@postgres:5432/kavach"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET: str = "dev-only-change-me"  # noqa: S105 — dev default, env-overridden
    PII_MASTER_KEY: str = "dev-only-32-bytes-change-me!!"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @property
    def effective_embed_mode(self) -> str:
        return self.EMBED_MODE or self.LLM_MODE

    def assert_live_allowed(self) -> None:
        """Double opt-in gate for real API usage (docs/06 §3)."""
        if self.LLM_MODE == "live" and self.LLM_LIVE_ACK != "yes":
            raise RuntimeError("LLM_MODE=live requires LLM_LIVE_ACK=yes — see docs/06 §3")


settings = Settings()
