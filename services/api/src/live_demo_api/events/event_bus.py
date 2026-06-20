"""Provider-agnostic event bus interface."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from live_demo_contracts.event import EventEnvelope

type EventStreamName = str


@dataclass(frozen=True)
class PublishedEvent:
    event_id: UUID | str
    stream_key: str
    redis_message_id: str


@dataclass(frozen=True)
class ReceivedEvent:
    event: EventEnvelope
    stream_key: str
    redis_message_id: str
    delivery_count: int


class EventBus(Protocol):
    async def publish(self, event: EventEnvelope) -> PublishedEvent: ...

    async def publish_many(self, events: Sequence[EventEnvelope]) -> list[PublishedEvent]: ...

    def subscribe(
        self,
        stream: EventStreamName,
        consumer_group: str,
        consumer_name: str,
        block_ms: int,
        count: int,
    ) -> AsyncIterator[ReceivedEvent]: ...

    async def acknowledge(
        self,
        stream: EventStreamName,
        consumer_group: str,
        message_id: str,
    ) -> None: ...
