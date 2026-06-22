"""Configuration for local and production observability."""

from __future__ import annotations

from dataclasses import dataclass
from os import environ


@dataclass(frozen=True)
class ObservabilityConfig:
    enabled: bool = True
    service_name: str = "live-demo-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    otel_enabled: bool = True
    otlp_endpoint: str = "http://otel-collector:4317"
    prometheus_enabled: bool = True
    log_format: str = "json"
    log_level: str = "info"
    latency_budget_enabled: bool = True
    latency_budget_warn_only: bool = True
    cardinality_guard_enabled: bool = True

    @classmethod
    def from_env(cls, *, service_name: str | None = None) -> ObservabilityConfig:
        return cls(
            enabled=_bool("OBSERVABILITY_ENABLED", True),
            service_name=service_name
            or _str("SERVICE_NAME", "")
            or _str("OTEL_SERVICE_NAME", "live-demo-service"),
            service_version=_str("SERVICE_VERSION", "0.1.0"),
            environment=_str("DEPLOYMENT_ENVIRONMENT", _str("APP_ENV", "local")),
            otel_enabled=_bool("OTEL_ENABLED", _bool("ENABLE_TRACING", True)),
            otlp_endpoint=_str("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"),
            prometheus_enabled=_bool("PROMETHEUS_ENABLED", True),
            log_format=_str("LOG_FORMAT", "json"),
            log_level=_str("LOG_LEVEL", "info"),
            latency_budget_enabled=_bool("LATENCY_BUDGET_ENABLED", True),
            latency_budget_warn_only=_bool("LATENCY_BUDGET_WARN_ONLY", True),
            cardinality_guard_enabled=_bool("PROMETHEUS_CARDINALITY_GUARD_ENABLED", True),
        )


def _str(name: str, default: str) -> str:
    value = environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def _bool(name: str, default: bool) -> bool:
    value = environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
