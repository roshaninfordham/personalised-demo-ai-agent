"""API tracing setup."""

from fastapi import FastAPI

from live_demo_backend_common.observability.config import ObservabilityConfig
from live_demo_backend_common.observability.tracing import setup_tracing


def configure_tracing(app: FastAPI, enabled: bool) -> None:
    config = ObservabilityConfig.from_env(service_name="api")
    setup_tracing(config.service_name, enabled=enabled)
    app.state.tracing_enabled = enabled
