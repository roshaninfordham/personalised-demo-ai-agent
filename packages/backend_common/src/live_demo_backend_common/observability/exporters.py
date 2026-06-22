"""Exporter setup placeholders that degrade gracefully."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExporterStatus:
    traces_enabled: bool
    metrics_enabled: bool
    logs_enabled: bool
    endpoint: str | None
    degraded: bool = False
    message: str = ""


def configure_exporters(
    *,
    traces_enabled: bool,
    metrics_enabled: bool,
    logs_enabled: bool,
    endpoint: str | None,
) -> ExporterStatus:
    if endpoint is None or endpoint == "":
        return ExporterStatus(
            traces_enabled=False,
            metrics_enabled=False,
            logs_enabled=logs_enabled,
            endpoint=None,
            degraded=True,
            message="OTLP endpoint not configured.",
        )
    return ExporterStatus(
        traces_enabled=traces_enabled,
        metrics_enabled=metrics_enabled,
        logs_enabled=logs_enabled,
        endpoint=endpoint,
    )
