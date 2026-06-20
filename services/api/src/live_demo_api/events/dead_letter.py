"""Dead-letter support for Redis Stream consumers."""

from __future__ import annotations

from datetime import UTC, datetime

from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.live_state.redis_keys import dead_letter_stream_key


async def write_dead_letter(
    redis: Redis[bytes],
    *,
    original_stream: str,
    original_message_id: str,
    event_json: str,
    error_message: str,
) -> str:
    message_id = await redis.xadd(
        dead_letter_stream_key(),
        {
            "original_stream": original_stream,
            "original_message_id": original_message_id,
            "event_json": event_json,
            "error_message": error_message,
            "failed_at": datetime.now(UTC).isoformat(),
        },
        maxlen=get_settings().redis_event_stream_maxlen,
        approximate=True,
    )
    return message_id.decode("utf-8") if isinstance(message_id, bytes) else str(message_id)
