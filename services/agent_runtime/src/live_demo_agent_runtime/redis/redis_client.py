"""Redis client factory."""

from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from live_demo_agent_runtime.config import get_settings


@lru_cache(maxsize=1)
def get_redis_client() -> Redis[str]:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


async def ping_redis() -> bool:
    return bool(await get_redis_client().ping())


async def close_redis_client() -> None:
    if get_redis_client.cache_info().currsize == 0:
        return
    await get_redis_client().close()
    get_redis_client.cache_clear()
