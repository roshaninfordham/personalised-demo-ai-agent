"""Redis Streams event publisher for voice runtime events."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import UUID, uuid4

from redis.asyncio import Redis

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.redis.redis_keys import stream_key


class RedisEventPublisher(EventPublisher):
    def __init__(self, redis: Redis[str], settings: AgentRuntimeSettings) -> None:
        self._redis = redis
        self._settings = settings

    async def publish(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        event_type: str,
        trace_id: str,
        payload: Mapping[str, object],
    ) -> str:
        event_id = str(uuid4())
        envelope = {
            "event_id": event_id,
            "organization_id": str(organization_id),
            "session_id": str(demo_session_id),
            "event_type": event_type,
            "created_at": datetime.now(UTC).isoformat(),
            "trace_id": trace_id,
            "payload": dict(payload),
        }
        fields = {"event": json.dumps(envelope, sort_keys=True, separators=(",", ":"))}
        await self._redis.xadd(
            stream_key(self._settings.redis_key_prefix, str(demo_session_id)),
            fields,
            maxlen=self._settings.redis_event_stream_maxlen,
            approximate=True,
        )
        return event_id


class InMemoryEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    async def publish(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        event_type: str,
        trace_id: str,
        payload: Mapping[str, object],
    ) -> str:
        event_id = str(uuid4())
        self.events.append(
            {
                "event_id": event_id,
                "organization_id": str(organization_id),
                "session_id": str(demo_session_id),
                "event_type": event_type,
                "trace_id": trace_id,
                "payload": dict(payload),
            }
        )
        return event_id
