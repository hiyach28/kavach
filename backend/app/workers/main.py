"""arq worker entrypoint. Jobs are added from Phase 2 (F20+)."""
from arq.connections import RedisSettings

from app.config import settings


async def ping(ctx: dict) -> str:  # smoke-test job
    return "pong"


class WorkerSettings:
    functions = [ping]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
