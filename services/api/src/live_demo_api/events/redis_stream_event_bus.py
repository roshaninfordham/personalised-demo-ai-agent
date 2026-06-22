"""Redis Streams implementation of the event bus."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from time import perf_counter_ns
from typing import Any

from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import ResponseError

from live_demo_api.config import get_settings
from live_demo_api.events.dead_letter import write_dead_letter
from live_demo_api.events.event_bus import EventStreamName, PublishedEvent, ReceivedEvent
from live_demo_api.live_state.redis_keys import global_events_stream_key, session_events_stream_key
from live_demo_backend_common.observability.metric_names import (
    EVENT_PUBLISH_LATENCY_SECONDS,
    EVENTS_PUBLISHED_TOTAL,
)
from live_demo_backend_common.observability.metrics import get_global_registry
from live_demo_backend_common.observability.tracing import get_current_span
from live_demo_contracts.event import EventEnvelope


class EventBusValidationError(ValueError):
    """Raised when an event payload cannot be validated against contracts."""


class RedisStreamEventBus:
    def __init__(
        self,
        redis: Redis[bytes],
        *,
        stream_maxlen: int | None = None,
        publish_global: bool | None = None,
    ) -> None:
        settings = get_settings()
        self._redis = redis
        self._stream_maxlen = stream_maxlen or settings.redis_event_stream_maxlen
        self._publish_global = (
            publish_global if publish_global is not None else settings.event_bus_publish_global
        )

    async def publish(self, event: EventEnvelope) -> PublishedEvent:
        event = self._validate(event)
        stream_keys = self._target_streams(event)
        first_published: PublishedEvent | None = None
        for stream_key in stream_keys:
            redis_message_id = await self._xadd(stream_key, event)
            published = PublishedEvent(
                event_id=event.event_id,
                stream_key=stream_key,
                redis_message_id=redis_message_id,
            )
            if first_published is None:
                first_published = published
        if first_published is None:
            raise EventBusValidationError("Event did not resolve to a target stream")
        return first_published

    async def publish_many(self, events: Sequence[EventEnvelope]) -> list[PublishedEvent]:
        published: list[PublishedEvent] = []
        for event in events:
            published.append(await self.publish(event))
        return published

    async def subscribe(
        self,
        stream: EventStreamName,
        consumer_group: str,
        consumer_name: str,
        block_ms: int,
        count: int,
    ) -> AsyncIterator[ReceivedEvent]:
        await self._ensure_group(stream, consumer_group)
        while True:
            response = await self._redis.xreadgroup(
                consumer_group,
                consumer_name,
                {stream: ">"},
                count=count,
                block=block_ms,
            )
            for stream_name, messages in response:
                stream_key = self._decode(stream_name)
                for message_id, fields in messages:
                    yield self._received_event(stream_key, message_id, fields)

    async def acknowledge(
        self,
        stream: EventStreamName,
        consumer_group: str,
        message_id: str,
    ) -> None:
        await self._redis.xack(stream, consumer_group, message_id)  # type: ignore[no-untyped-call]

    async def dead_letter(
        self,
        *,
        original_stream: str,
        original_message_id: str,
        event_json: str,
        error_message: str,
    ) -> str:
        return await write_dead_letter(
            self._redis,
            original_stream=original_stream,
            original_message_id=original_message_id,
            event_json=event_json,
            error_message=error_message,
        )

    def _target_streams(self, event: EventEnvelope) -> list[str]:
        stream_keys: list[str] = []
        if event.session_id is not None:
            stream_keys.append(session_events_stream_key(event.session_id))
        if self._publish_global or event.session_id is None:
            stream_keys.append(global_events_stream_key())
        return stream_keys

    async def _xadd(self, stream_key: str, event: EventEnvelope) -> str:
        event_json = event.model_dump_json()
        span = get_current_span()
        start_ns = perf_counter_ns()
        message_id = await self._redis.xadd(
            stream_key,
            {
                "event_json": event_json,
                "event_type": event.event_type,
                "trace_id": event.trace_id,
                "traceparent": span.trace_context.traceparent if span else "",
                "span_id": span.span_id if span else "",
            },
            maxlen=self._stream_maxlen,
            approximate=True,
        )
        elapsed_seconds = (perf_counter_ns() - start_ns) / 1_000_000_000
        group = str(event.event_type).split(".")[0]
        registry = get_global_registry()
        registry.increment(
            EVENTS_PUBLISHED_TOTAL,
            labels={"event_type_group": group, "result": "success"},
        )
        registry.observe(
            EVENT_PUBLISH_LATENCY_SECONDS,
            elapsed_seconds,
            labels={"event_type_group": group, "result": "success"},
        )
        return self._decode(message_id)

    async def _ensure_group(self, stream: str, consumer_group: str) -> None:
        try:
            await self._redis.xgroup_create(stream, consumer_group, id="0", mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def _received_event(
        self,
        stream_key: str,
        message_id: bytes | str,
        fields: dict[Any, Any],
    ) -> ReceivedEvent:
        event_json = self._field(fields, "event_json")
        try:
            event = EventEnvelope.model_validate_json(event_json)
        except ValidationError as exc:
            raise EventBusValidationError("Invalid event payload from Redis Stream") from exc
        return ReceivedEvent(
            event=event,
            stream_key=stream_key,
            redis_message_id=self._decode(message_id),
            delivery_count=1,
        )

    def _validate(self, event: EventEnvelope) -> EventEnvelope:
        try:
            return EventEnvelope.model_validate(event.model_dump(mode="json"))
        except ValidationError as exc:
            raise EventBusValidationError("Invalid event envelope") from exc

    def _field(self, fields: dict[Any, Any], name: str) -> str:
        for key, value in fields.items():
            if self._decode(key) == name:
                return self._decode(value)
        raise EventBusValidationError(f"Redis Stream message missing field: {name}")

    def _decode(self, value: bytes | str | object) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        if isinstance(value, str):
            return value
        return json.dumps(value, sort_keys=True)
