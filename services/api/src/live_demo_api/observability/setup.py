"""API observability bootstrap."""

from __future__ import annotations

from live_demo_api.config import ApiSettings
from live_demo_api.observability.metrics import configure_metrics
from live_demo_backend_common.observability.config import ObservabilityConfig
from live_demo_backend_common.observability.logging import configure_json_logging
from live_demo_backend_common.observability.tracing import setup_tracing

_configured = False


def setup_observability(settings: ApiSettings) -> None:
    global _configured
    if _configured:
        return
    config = ObservabilityConfig.from_env(service_name="api")
    configure_metrics()
    setup_tracing(config.service_name, enabled=settings.enable_tracing)
    configure_json_logging(
        service=config.service_name,
        environment=config.environment,
        log_level=settings.log_level,
    )
    _configured = True
