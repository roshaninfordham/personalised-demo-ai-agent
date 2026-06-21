from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from uuid import uuid4

from live_demo_api.events.event_bus import PublishedEvent, ReceivedEvent
from live_demo_api.orchestration.orchestration_events import publish_orchestration_event
from live_demo_api.security import RequestContext
from live_demo_contracts.event import EventEnvelope


class CapturingEventBus:
    def __init__(self) -> None:
        self.events: list[EventEnvelope] = []

    async def publish(self, event: EventEnvelope) -> PublishedEvent:
        self.events.append(event)
        return PublishedEvent(event_id=event.event_id, stream_key="stream", redis_message_id="1-0")

    async def publish_many(self, events: Sequence[EventEnvelope]) -> list[PublishedEvent]:
        return [await self.publish(event) for event in events]

    def subscribe(
        self,
        stream: str,
        consumer_group: str,
        consumer_name: str,
        block_ms: int,
        count: int,
    ) -> AsyncIterator[ReceivedEvent]:
        _ = stream, consumer_group, consumer_name, block_ms, count
        raise NotImplementedError

    async def acknowledge(self, stream: str, consumer_group: str, message_id: str) -> None:
        _ = stream, consumer_group, message_id


async def test_orchestration_event_payload_redacts_secret_keys() -> None:
    bus = CapturingEventBus()

    await publish_orchestration_event(
        bus,
        organization_id=uuid4(),
        session_id=uuid4(),
        event_type="session.readiness.updated",
        request_context=RequestContext(request_id="req", trace_id="trace"),
        payload={"score": 1.0, "provider_token": "secret"},
    )

    assert bus.events[0].payload == {"score": 1.0}
