"""Structured JSON logging with trace correlation and redaction."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from live_demo_backend_common.observability.redaction import redact_mapping, safe_error_message
from live_demo_backend_common.observability.tracing import get_current_span


class JsonLogFormatter(logging.Formatter):
    def __init__(self, *, service: str, environment: str) -> None:
        super().__init__()
        self._service = service
        self._environment = environment

    def format(self, record: logging.LogRecord) -> str:
        span = get_current_span()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "service": self._service,
            "environment": self._environment,
            "event_type": getattr(record, "event_type", record.getMessage()),
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", None) or (span.trace_id if span else None),
            "span_id": getattr(record, "span_id", None) or (span.span_id if span else None),
            "request_id": getattr(record, "request_id", None),
            "organization_id": getattr(record, "organization_id", None),
            "session_id": getattr(record, "session_id", None),
            "turn_id": getattr(record, "turn_id", None),
            "component": getattr(record, "component", record.name),
            "operation": getattr(record, "operation", None),
            "latency_ms": getattr(record, "latency_ms", None),
            "success": getattr(record, "success", None),
            "error": _safe_error(record),
            "metadata": {},
        }
        metadata: dict[str, object] = {}
        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_KEYS or key in payload:
                continue
            if key.startswith("_"):
                continue
            metadata[key] = value
        payload["metadata"] = redact_mapping(metadata)
        return json.dumps(redact_mapping(payload), sort_keys=True, default=str)


def configure_json_logging(*, service: str, environment: str, log_level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter(service=service, environment=environment))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(log_level.upper())


def log_event(
    logger: logging.Logger,
    *,
    event_type: str,
    message: str,
    level: int = logging.INFO,
    **fields: object,
) -> None:
    logger.log(level, message, extra={"event_type": event_type, **fields})


def _safe_error(record: logging.LogRecord) -> dict[str, object] | None:
    error = getattr(record, "error", None)
    if isinstance(error, dict):
        return redact_mapping(error)
    if record.exc_info is None:
        return None
    exc_type = record.exc_info[0]
    exc = record.exc_info[1]
    return {
        "code": getattr(exc, "code", "unknown_error"),
        "message": safe_error_message(str(exc)),
        "type": exc_type.__name__ if exc_type is not None else "Exception",
        "retryable": bool(getattr(exc, "retryable", False)),
    }


_RESERVED_LOG_RECORD_KEYS = {
    "args",
    "msg",
    "exc_info",
    "exc_text",
    "stack_info",
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
}
