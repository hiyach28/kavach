import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logger = logging.getLogger("kavach")

app = FastAPI(title="KAVACH API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness — no dependencies."""
    return {"status": "ok", "env": settings.ENV, "llm_mode": settings.LLM_MODE}


@app.get("/health/deep")
async def health_deep() -> dict[str, str]:
    """Readiness — checks Postgres and Redis."""
    import redis.asyncio as aioredis
    from sqlalchemy import create_engine, text

    result = {"api": "ok", "postgres": "fail", "redis": "fail"}
    try:
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["postgres"] = "ok"
    except Exception as exc:  # noqa: BLE001 — health endpoint reports, never raises
        logger.warning("health: postgres check failed: %s", exc)
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        result["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        logger.warning("health: redis check failed: %s", exc)
    result["status"] = "ok" if all(v == "ok" for v in result.values()) else "degraded"
    return result
