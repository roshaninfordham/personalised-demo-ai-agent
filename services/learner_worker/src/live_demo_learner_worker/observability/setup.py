"""Learner worker observability setup."""

from __future__ import annotations

from live_demo_backend_common.observability.config import ObservabilityConfig
from live_demo_backend_common.observability.logging import configure_json_logging
from live_demo_backend_common.observability.metrics import configure_global_registry
from live_demo_backend_common.observability.tracing import setup_tracing
from live_demo_learner_worker.config import LearnerWorkerSettings

_configured = False


def setup_observability(settings: LearnerWorkerSettings) -> None:
    global _configured
    if _configured:
        return
    config = ObservabilityConfig.from_env(service_name="learner-worker")
    configure_global_registry(
        service=config.service_name,
        environment=config.environment,
        guard_enabled=config.cardinality_guard_enabled,
    )
    setup_tracing(config.service_name, enabled=config.otel_enabled)
    configure_json_logging(
        service=config.service_name,
        environment=config.environment,
        log_level=settings.log_level,
    )
    _configured = True
