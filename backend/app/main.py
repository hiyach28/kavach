import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.config import settings
from app.core.errors import KavachException, kavach_exception_handler, unhandled_exception_handler
from app.core.middleware import RequestMiddleware, limiter, rate_limit_exceeded_handler

logger = logging.getLogger("kavach")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="2.0.0",
)

# ── Phase 1: Middleware & Exception Handlers ────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_exception_handler(KavachException, kavach_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(RequestMiddleware)

# ── API Routers ─────────────────────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_STR)

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
        r = aioredis.from_url(settings.REDIS_URL)  # type: ignore[no-untyped-call]
        await r.ping()
        await r.aclose()
        result["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        logger.warning("health: redis check failed: %s", exc)
    result["status"] = "ok" if all(v == "ok" for v in result.values()) else "degraded"
    return result
