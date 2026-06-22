"""API metrics backed by the shared observability registry."""

from live_demo_backend_common.observability import metric_names
from live_demo_backend_common.observability.config import ObservabilityConfig
from live_demo_backend_common.observability.metrics import (
    MetricRegistry,
    configure_global_registry,
    get_global_registry,
)


def configure_metrics() -> MetricRegistry:
    config = ObservabilityConfig.from_env(service_name="api")
    return configure_global_registry(
        service=config.service_name,
        environment=config.environment,
        guard_enabled=config.cardinality_guard_enabled,
    )


class ApiMetrics:
    def record_request(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        _ = path
        status = "success" if status_code < 500 else "failed"
        registry = get_global_registry()
        registry.increment(
            metric_names.EVENTS_PUBLISHED_TOTAL,
            labels={"event_type_group": "http", "result": status},
        )
        registry.observe(
            metric_names.TURN_LATENCY_SECONDS,
            duration_ms / 1000,
            labels={"phase": "http_request"},
        )
        if status == "failed":
            registry.increment(
                metric_names.ERRORS_TOTAL,
                labels={
                    "component": "http",
                    "error_code": "http_5xx",
                    "severity": "error",
                },
            )

    def prometheus_text(self) -> str:
        return get_global_registry().render_prometheus()

metrics = ApiMetrics()
