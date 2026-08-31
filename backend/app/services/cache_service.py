"""Redis caching layer for frequently accessed data."""

import json
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    global _pool
    if _pool is None:
        try:
            _pool = aioredis.from_url(settings.redis_url, decode_responses=True)
            await _pool.ping()
        except Exception as e:
            logger.warning("redis_unavailable", error=str(e))
            _pool = None
    return _pool


async def cache_get(key: str) -> Any | None:
    client = await get_redis()
    if not client:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning("cache_get_failed", key=key, error=str(e))
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    client = await get_redis()
    if not client:
        return
    try:
        await client.setex(key, ttl_seconds, json.dumps(value, default=str))
    except Exception as e:
        logger.warning("cache_set_failed", key=key, error=str(e))


async def cache_delete_pattern(pattern: str) -> None:
    client = await get_redis()
    if not client:
        return
    try:
        keys = [k async for k in client.scan_iter(match=pattern)]
        if keys:
            await client.delete(*keys)
    except Exception as e:
        logger.warning("cache_delete_failed", pattern=pattern, error=str(e))
