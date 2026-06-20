"""Consumer idempotency helpers."""

from __future__ import annotations

from uuid import UUID

from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.live_state.redis_keys import processed_event_key


async def was_event_processed(
    redis: Redis[bytes], event_id: UUID | str, consumer_name: str
) -> bool:
    return await redis.exists(processed_event_key(consumer_name, event_id)) == 1


async def mark_event_processed(
    redis: Redis[bytes], event_id: UUID | str, consumer_name: str
) -> None:
    ttl_seconds = get_settings().event_bus_processed_event_ttl_seconds
    await redis.setex(processed_event_key(consumer_name, event_id), ttl_seconds, "1")
