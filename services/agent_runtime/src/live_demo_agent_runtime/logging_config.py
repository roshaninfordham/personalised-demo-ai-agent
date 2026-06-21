"""Structured logging for the agent runtime."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "api_key",
    "token",
    "secret",
    "password",
    "daily_api_key",
    "deepgram_api_key",
    "cartesia_api_key",
    "ai_stt_api_key",
    "ai_tts_api_key",
}


def redact_value(key: str, value: object) -> object:
    lower = key.lower()
    if lower in SENSITIVE_KEYS or "secret" in lower or "token" in lower or "api_key" in lower:
        return "***REDACTED***"
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
            "service": "agent-runtime",
        }
        for key in (
            "request_id",
            "trace_id",
            "voice_session_id",
            "demo_session_id",
            "organization_id",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = redact_value(key, value)
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
