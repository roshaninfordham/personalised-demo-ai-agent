from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.events.consumer import mark_event_processed, was_event_processed
from live_demo_api.events.redis_stream_event_bus import EventBusValidationError, RedisStreamEventBus
from live_demo_api.live_state.redis_keys import (
    dead_letter_stream_key,
    global_events_stream_key,
    session_events_stream_key,
)
from live_demo_contracts.event import EventEnvelope, EventType

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def redis_client() -> AsyncIterator[Redis[bytes]]:
    client = Redis.from_url(get_settings().redis_url)
    try:
        yield client
    finally:
        await client.close()


def _event(session_id: str, organization_id: str) -> EventEnvelope:
    return EventEnvelope(
        event_id=str(uuid4()),
        session_id=session_id,
        organization_id=organization_id,
        event_type=EventType.SESSION_CREATED,
        created_at=datetime.now(UTC).isoformat(),
        trace_id=f"trace_{uuid4().hex}",
        payload={"source": "test"},
    )


async def test_publish_consume_ack_and_global_fanout(redis_client: Redis[bytes]) -> None:
    session_id = str(uuid4())
    organization_id = str(uuid4())
    event = _event(session_id, organization_id)
    stream_key = session_events_stream_key(session_id)
    group_name = f"group-{uuid4().hex}"
    consumer_name = f"consumer-{uuid4().hex}"
    bus = RedisStreamEventBus(redis_client, publish_global=True)

    published = await bus.publish(event)
    assert published.stream_key == stream_key

    assert await redis_client.xlen(stream_key) == 1
    assert await redis_client.xlen(global_events_stream_key()) >= 1

    iterator = bus.subscribe(stream_key, group_name, consumer_name, block_ms=100, count=1)
    received = await anext(iterator)
    assert received.event.event_id == event.event_id

    await bus.acknowledge(stream_key, group_name, received.redis_message_id)
    pending = await redis_client.xpending(stream_key, group_name)  # type: ignore[no-untyped-call]
    assert pending["pending"] == 0


async def test_invalid_event_payload_raises(redis_client: Redis[bytes]) -> None:
    stream_key = session_events_stream_key(uuid4())
    group_name = f"group-{uuid4().hex}"
    bus = RedisStreamEventBus(redis_client)
    await redis_client.xadd(
        stream_key, {"event_json": "{}", "event_type": "error", "trace_id": "trace"}
    )

    iterator = bus.subscribe(stream_key, group_name, "consumer", block_ms=100, count=1)
    with pytest.raises(EventBusValidationError):
        await anext(iterator)


async def test_dead_letter_and_idempotency(redis_client: Redis[bytes]) -> None:
    bus = RedisStreamEventBus(redis_client)
    original_stream = session_events_stream_key(uuid4())
    message_id = await bus.dead_letter(
        original_stream=original_stream,
        original_message_id="1-0",
        event_json='{"event_id":"bad"}',
        error_message="boom",
    )
    assert message_id
    assert await redis_client.xlen(dead_letter_stream_key()) >= 1

    event_id = uuid4()
    consumer_name = "api-test-consumer"
    assert not await was_event_processed(redis_client, event_id, consumer_name)
    await mark_event_processed(redis_client, event_id, consumer_name)
    assert await was_event_processed(redis_client, event_id, consumer_name)


async def test_stream_max_length_is_applied(redis_client: Redis[bytes]) -> None:
    session_id = str(uuid4())
    organization_id = str(uuid4())
    bus = RedisStreamEventBus(redis_client, stream_maxlen=2, publish_global=False)
    for _ in range(20):
        await bus.publish(_event(session_id, organization_id))
    assert await redis_client.xlen(session_events_stream_key(session_id)) <= 20
