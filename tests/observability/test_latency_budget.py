from live_demo_backend_common.observability.latency_budget import DEFAULT_LATENCY_BUDGETS
from live_demo_backend_common.observability.latency_enforcer import LatencyEnforcer
from live_demo_backend_common.observability.metrics import MetricRegistry
from live_demo_backend_common.observability.tracing import get_finished_spans, start_span


def test_duration_below_target_is_ok() -> None:
    result = LatencyEnforcer(metrics=_registry()).check("context_build", 10)

    assert result.status == "ok"
    assert result.severity == "none"


def test_duration_between_warning_and_critical_is_violation() -> None:
    result = LatencyEnforcer(metrics=_registry()).check("context_build", 150)

    assert result.status == "violated"
    assert result.severity == "violated"


def test_duration_above_critical_is_critical() -> None:
    result = LatencyEnforcer(metrics=_registry()).check(
        "context_build", 300, context={"session_id": "session-test"}
    )

    assert result.status == "critical"
    assert result.severity == "critical"


def test_budget_violation_adds_span_event() -> None:
    with start_span("turn.process"):
        LatencyEnforcer(metrics=_registry()).check("context_build", 300)

    assert any(
        event.name == "latency_budget.violation"
        for span in get_finished_spans()
        for event in span.events
    )


def test_repeated_critical_marks_session_degraded() -> None:
    enforcer = LatencyEnforcer(metrics=_registry())
    for _ in range(3):
        enforcer.check("context_build", 300, context={"session_id": "session-test"})

    assert enforcer.is_session_degraded("session-test", "context_build")
    assert DEFAULT_LATENCY_BUDGETS["context_build"].target_ms == 50


def _registry() -> MetricRegistry:
    return MetricRegistry(service="test", environment="local")
