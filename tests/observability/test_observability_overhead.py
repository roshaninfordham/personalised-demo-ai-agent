from __future__ import annotations

import statistics
import time

from live_demo_backend_common.observability.latency_enforcer import LatencyEnforcer
from live_demo_backend_common.observability.metrics import MetricRegistry
from live_demo_backend_common.observability.trace_context import TraceContext
from live_demo_backend_common.observability.tracing import (
    clear_finished_spans,
    start_span,
)

ITERATIONS = 500


def test_observability_hot_path_overhead_targets() -> None:
    registry = MetricRegistry(service="test", environment="local")
    enforcer = LatencyEnforcer(metrics=registry)
    registry.observe("live_demo_turn_latency_seconds", 0.001, labels={"phase": "overview"})

    span_ms = _median_ms(_create_span_once)
    metric_ms = _median_ms(
        lambda: registry.observe(
            "live_demo_turn_latency_seconds", 0.001, labels={"phase": "overview"}
        )
    )
    budget_ms = _median_ms(lambda: enforcer.check("context_build", 1.0))
    context_ms = _median_ms(_propagate_context_once)

    assert span_ms <= 0.1
    assert metric_ms <= 0.05
    assert budget_ms <= 0.05
    assert context_ms <= 0.1


def _median_ms(callable_object) -> float:  # type: ignore[no-untyped-def]
    durations: list[float] = []
    for _ in range(ITERATIONS):
        started = time.perf_counter_ns()
        callable_object()
        durations.append((time.perf_counter_ns() - started) / 1_000_000)
    return statistics.median(durations)


def _create_span_once() -> None:
    clear_finished_spans()
    with start_span("turn.process"):
        pass


def _propagate_context_once() -> None:
    context = TraceContext.new()
    headers = context.inject_headers()
    TraceContext.from_headers(headers)
