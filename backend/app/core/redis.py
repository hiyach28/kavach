"""Redis and arq configuration for async worker queue."""

from typing import Any

from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings

# Global arq Redis pool for enqueuing jobs
redis_pool: Any = None


def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into arq RedisSettings."""
    # settings.REDIS_URL is something like "redis://redis:6379/0"
    return RedisSettings.from_dsn(settings.REDIS_URL)


async def init_redis_pool() -> None:
    """Initialize the arq Redis pool. Call on startup."""
    global redis_pool
    if redis_pool is None:
        redis_settings = get_redis_settings()
        redis_pool = await create_pool(redis_settings)


async def close_redis_pool() -> None:
    """Close the arq Redis pool. Call on shutdown."""
    global redis_pool
    if redis_pool is not None:
        await redis_pool.close()
        redis_pool = None
