"""Redis Stream post-demo job enqueue helper."""

from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.post_demo.post_demo_job_types import PostDemoJobEnvelope


class PostDemoJobQueue:
    def __init__(self, redis: Redis[bytes]) -> None:
        self._redis = redis

    async def enqueue(self, envelope: PostDemoJobEnvelope) -> str:
        payload: dict[str, Any] = {
            "job_id": str(envelope.job_id),
            "organization_id": str(envelope.organization_id),
            "session_id": str(envelope.session_id),
            "job_type": envelope.job_type,
            "attempt": envelope.attempt,
            "max_attempts": envelope.max_attempts,
            "idempotency_key": envelope.idempotency_key,
            "created_at": envelope.created_at.isoformat(),
            "trace_id": envelope.trace_id,
            "payload": json.dumps(envelope.payload, sort_keys=True),
        }
        message_id = await self._redis.xadd(
            get_settings().post_demo_job_stream,
            payload,
            maxlen=get_settings().redis_event_stream_maxlen,
            approximate=True,
        )
        return message_id.decode() if isinstance(message_id, bytes) else str(message_id)
