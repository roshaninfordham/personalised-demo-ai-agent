"""Lightweight OpenTelemetry-compatible span facade.

The facade works without an exporter so tests and local runs never depend on a paid
observability vendor. It preserves W3C trace context and can be swapped for a full
OpenTelemetry SDK exporter later without changing service instrumentation.
"""

from __future__ import annotations

import contextvars
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field

from live_demo_backend_common.observability.redaction import redact_mapping, safe_error_message
from live_demo_backend_common.observability.trace_context import TraceContext


@dataclass
class SpanEvent:
    name: str
    attributes: dict[str, object]
    monotonic_time_ns: int


@dataclass
class ObservedSpan:
    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    attributes: dict[str, object] = field(default_factory=dict)
    events: list[SpanEvent] = field(default_factory=list)
    status: str = "ok"
    error_code: str | None = None
    started_ns: int = field(default_factory=time.perf_counter_ns)
    ended_ns: int | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.ended_ns is None:
            return None
        return (self.ended_ns - self.started_ns) / 1_000_000

    @property
    def trace_context(self) -> TraceContext:
        return TraceContext(trace_id=self.trace_id, span_id=self.span_id)

    def add_event(self, name: str, attributes: Mapping[str, object] | None = None) -> None:
        self.events.append(
            SpanEvent(
                name=name,
                attributes=redact_mapping(attributes or {}),
                monotonic_time_ns=time.perf_counter_ns(),
            )
        )

    def set_attribute(self, key: str, value: object) -> None:
        self.attributes.update(redact_mapping({key: value}))

    def mark_error(self, error_code: str, message: str | None = None) -> None:
        self.status = "error"
        self.error_code = error_code
        attributes: dict[str, object] = {"error_code": error_code}
        if message:
            attributes["message"] = safe_error_message(message)
        self.add_event("exception", attributes)

    def end(self) -> None:
        if self.ended_ns is None:
            self.ended_ns = time.perf_counter_ns()


_active_span: contextvars.ContextVar[ObservedSpan | None] = contextvars.ContextVar(
    "live_demo_active_span", default=None
)
_finished_spans: list[ObservedSpan] = []
_configured_services: set[str] = set()


def setup_tracing(service_name: str, *, enabled: bool = True) -> None:
    if not enabled:
        return
    _configured_services.add(service_name)


def get_current_span() -> ObservedSpan | None:
    return _active_span.get()


def get_current_trace_context() -> TraceContext:
    span = get_current_span()
    if span is not None:
        return span.trace_context
    return TraceContext.new()


@contextmanager
def start_span(
    name: str,
    *,
    trace_context: TraceContext | None = None,
    attributes: Mapping[str, object] | None = None,
) -> Iterator[ObservedSpan]:
    parent = _active_span.get()
    base_context = trace_context or (
        parent.trace_context if parent is not None else TraceContext.new()
    )
    child_context = (
        base_context.child() if parent is not None or trace_context is not None else base_context
    )
    parent_span_id = (
        parent.span_id
        if parent is not None
        else trace_context.span_id
        if trace_context is not None
        else None
    )
    span = ObservedSpan(
        name=name,
        trace_id=child_context.trace_id,
        span_id=child_context.span_id,
        parent_span_id=parent_span_id,
        attributes=redact_mapping(attributes or {}),
    )
    token = _active_span.set(span)
    try:
        yield span
    except Exception as exc:
        span.mark_error(type(exc).__name__, str(exc))
        raise
    finally:
        span.end()
        _finished_spans.append(span)
        _active_span.reset(token)


def add_span_event(name: str, attributes: Mapping[str, object] | None = None) -> None:
    span = get_current_span()
    if span is not None:
        span.add_event(name, attributes)


def get_finished_spans() -> tuple[ObservedSpan, ...]:
    return tuple(_finished_spans)


def clear_finished_spans() -> None:
    _finished_spans.clear()


def safe_span_attributes(attributes: Mapping[str, object]) -> dict[str, object]:
    return redact_mapping(attributes)
