from live_demo_backend_common.observability import metric_names, span_names
from live_demo_backend_common.observability.latency_enforcer import LatencyEnforcer
from live_demo_backend_common.observability.metrics import MetricRegistry
from live_demo_backend_common.observability.tracing import (
    clear_finished_spans,
    get_finished_spans,
    start_span,
)


def test_fake_session_run_produces_trace_metrics_and_budget_violation() -> None:
    clear_finished_spans()
    registry = MetricRegistry(service="agent-runtime", environment="local")
    enforcer = LatencyEnforcer(metrics=registry)

    with start_span(span_names.SESSION_PREWARM):
        with start_span(span_names.BROWSER_READ_SCREEN):
            registry.observe(
                metric_names.BROWSER_SCREEN_READ_LATENCY_SECONDS,
                0.1,
                {"result": "success"},
            )
        with start_span(span_names.TURN_PROCESS):
            with start_span(span_names.TURN_LLM_REQUEST):
                registry.observe(
                    metric_names.LLM_LATENCY_SECONDS,
                    3.5,
                    {"provider": "fake", "purpose": "realtime_host", "result": "success"},
                )
                enforcer.check("llm_realtime_host", 3500, context={"session_id": "session"})
            with start_span(span_names.BROWSER_ACTION_EXECUTE):
                registry.increment(
                    metric_names.BROWSER_ACTIONS_TOTAL,
                    labels={
                        "action_type": "click_element",
                        "risk_level": "low",
                        "result": "success",
                    },
                )

    output = registry.render_prometheus()
    assert metric_names.BROWSER_ACTIONS_TOTAL in output
    assert metric_names.LATENCY_BUDGET_VIOLATIONS_TOTAL in output
    assert {span.name for span in get_finished_spans()} >= {
        span_names.SESSION_PREWARM,
        span_names.TURN_PROCESS,
        span_names.BROWSER_ACTION_EXECUTE,
    }
