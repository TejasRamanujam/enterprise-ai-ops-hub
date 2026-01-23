import redis.asyncio as aioredis
from typing import Optional, Any
import json
import structlog

from app.core.config import settings

logger = structlog.get_logger()

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def cache_set(key: str, value: Any, ttl: int = settings.REDIS_CACHE_TTL) -> None:
    redis = await get_redis()
    serialized = json.dumps(value, default=str)
    await redis.setex(key, ttl, serialized)


async def cache_get(key: str) -> Optional[Any]:
    redis = await get_redis()
    data = await redis.get(key)
    if data:
        return json.loads(data)
    return None


async def cache_delete(key: str) -> None:
    redis = await get_redis()
    await redis.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    redis = await get_redis()
    keys = await redis.keys(pattern)
    if keys:
        await redis.delete(*keys)


async def rate_limit_check(
    identifier: str,
    max_requests: int = settings.RATE_LIMIT_REQUESTS,
    window: int = settings.RATE_LIMIT_WINDOW,
) -> tuple[bool, int]:
    redis = await get_redis()
    key = f"rate_limit:{identifier}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, window)
    remaining = max(0, max_requests - current)
    return current <= max_requests, remaining


async def publish_event(channel: str, event: dict) -> None:
    redis = await get_redis()
    await redis.publish(channel, json.dumps(event, default=str))


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
