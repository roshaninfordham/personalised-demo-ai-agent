"""Redis hash accessors for compact latency state."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.live_state.redis_keys import latency_key


class LatencyStore:
    def __init__(self, redis: Redis[bytes], *, ttl_seconds: int | None = None) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds or get_settings().redis_session_ttl_seconds

    async def set_latency_fields(
        self, session_id: UUID | str, values: Mapping[str, str | int]
    ) -> None:
        key = latency_key(session_id)
        await self._redis.hset(key, mapping={name: str(value) for name, value in values.items()})
        await self._redis.expire(key, self._ttl_seconds)

    async def get_latency_state(self, session_id: UUID | str) -> dict[str, str]:
        raw = await self._redis.hgetall(latency_key(session_id))
        result: dict[str, str] = {}
        for key, value in raw.items():
            key_text = key.decode("utf-8") if isinstance(key, bytes) else str(key)
            value_text = value.decode("utf-8") if isinstance(value, bytes) else str(value)
            result[key_text] = value_text
        return result
