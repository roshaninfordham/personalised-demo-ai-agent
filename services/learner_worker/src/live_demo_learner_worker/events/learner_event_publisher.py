"""Redis Stream event publisher for learner events."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from redis.asyncio import Redis


@dataclass(frozen=True, slots=True)
class LearnerEvent:
    event_id: UUID
    event_type: str
    organization_id: UUID
    product_id: UUID
    learning_run_id: UUID | None
    session_id: UUID | None
    trace_id: str
    payload: dict[str, object]
    created_at: datetime

    def to_json(self) -> str:
        return json.dumps(
            {
                "event_id": str(self.event_id),
                "event_type": self.event_type,
                "organization_id": str(self.organization_id),
                "product_id": str(self.product_id),
                "learning_run_id": (
                    str(self.learning_run_id) if self.learning_run_id is not None else None
                ),
                "session_id": str(self.session_id) if self.session_id is not None else None,
                "trace_id": self.trace_id,
                "payload": self.payload,
                "created_at": self.created_at.isoformat(),
            },
            sort_keys=True,
            default=str,
        )


class LearnerEventPublisher:
    def __init__(self, redis: Redis[bytes], stream_maxlen: int = 10000) -> None:
        self._redis = redis
        self._stream_maxlen = stream_maxlen

    async def publish(
        self,
        *,
        event_type: str,
        organization_id: UUID,
        product_id: UUID,
        learning_run_id: UUID | None,
        session_id: UUID | None,
        trace_id: str,
        payload: dict[str, object] | None = None,
    ) -> str:
        event = LearnerEvent(
            event_id=uuid4(),
            event_type=event_type,
            organization_id=organization_id,
            product_id=product_id,
            learning_run_id=learning_run_id,
            session_id=session_id,
            trace_id=trace_id,
            payload=payload or {},
            created_at=datetime.now(UTC),
        )
        stream_keys = ["live_demo:stream:global:events"]
        if session_id is not None:
            stream_keys.insert(0, f"live_demo:stream:session:{session_id}:events")
        message_id = "0-0"
        for stream in stream_keys:
            raw_id: Any = await self._redis.xadd(
                stream,
                {"event_json": event.to_json(), "event_type": event.event_type},
                maxlen=self._stream_maxlen,
                approximate=True,
            )
            message_id = raw_id.decode() if isinstance(raw_id, bytes) else str(raw_id)
        return message_id
