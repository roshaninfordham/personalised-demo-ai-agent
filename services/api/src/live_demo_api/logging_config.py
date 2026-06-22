"""JSON logging setup with deterministic secret redaction."""

from __future__ import annotations

import contextvars
import json
import logging
from datetime import UTC, datetime
from typing import Any

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
trace_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("trace_id", default=None)

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "api_key",
    "access_token",
    "refresh_token",
    "jwt_secret",
    "session_secret",
    "password",
    "secret",
    "object_storage_secret_key",
    "ai_text_api_key",
    "ai_stt_api_key",
    "ai_tts_api_key",
}


def redact_value(key: str, value: object) -> object:
    lowered = key.lower()
    if lowered in SENSITIVE_KEYS or "secret" in lowered or "token" in lowered:
        return "***REDACTED***"
    return value


def redact_mapping(values: dict[str, object]) -> dict[str, object]:
    redacted: dict[str, object] = {}
    for key, value in values.items():
        if isinstance(value, dict):
            redacted[key] = redact_mapping(value)
        else:
            redacted[key] = redact_value(key, value)
    return redacted


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event_type": getattr(
                record, "event_type", getattr(record, "event", record.getMessage())
            ),
            "message": record.getMessage(),
            "service": "api",
            "environment": "local",
            "request_id": request_id_var.get(),
            "trace_id": trace_id_var.get(),
            "span_id": getattr(record, "span_id", None),
            "component": getattr(record, "component", record.name),
            "operation": getattr(record, "operation", None),
            "latency_ms": getattr(record, "latency_ms", None),
            "success": getattr(record, "success", None),
            "error": getattr(record, "error", None),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in payload:
                continue
            if key in {"args", "msg", "exc_info", "exc_text", "stack_info"}:
                continue
            if key in {
                "name",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "taskName",
            }:
                continue
            payload[key] = redact_value(key, value)
        return json.dumps(payload, sort_keys=True, default=str)


def configure_logging(log_level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level.upper())
