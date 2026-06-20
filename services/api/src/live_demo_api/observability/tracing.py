"""Tracing hooks prepared for OpenTelemetry instrumentation."""

from fastapi import FastAPI


def configure_tracing(app: FastAPI, enabled: bool) -> None:
    app.state.tracing_enabled = enabled
