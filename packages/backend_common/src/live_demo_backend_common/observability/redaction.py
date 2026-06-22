"""Telemetry redaction helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

REDACTED = "***REDACTED***"

SENSITIVE_KEY_RE = re.compile(
    r"(authorization|cookie|set-cookie|api[_-]?key|access[_-]?token|refresh[_-]?token|"
    r"jwt|password|secret|private[_-]?key|prompt|completion|transcript|audio|screenshot|"
    r"html|dom)",
    re.IGNORECASE,
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(bearer\s+[a-z0-9._~-]+|sk-[a-z0-9]{12,}|"
    r"api[_-]?key\s*[:=]\s*['\"]?[a-z0-9._~-]{12,}|"
    r"password\s*[:=]\s*['\"]?[^'\"\s]{6,})"
)
URL_QUERY_RE = re.compile(r"([?&])([^=#&]+)=([^&#]+)")


def redact_string(value: str) -> str:
    without_secrets = SECRET_VALUE_RE.sub(REDACTED, value)
    return URL_QUERY_RE.sub(
        lambda match: f"{match.group(1)}{match.group(2)}={REDACTED}",
        without_secrets,
    )


def redact_value(key: str, value: object) -> object:
    if SENSITIVE_KEY_RE.search(key):
        return REDACTED
    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [redact_value(key, item) for item in value]
    return value


def redact_mapping(values: Mapping[str, object]) -> dict[str, object]:
    return {key: redact_value(key, value) for key, value in values.items()}


def safe_error_message(message: str) -> str:
    return redact_string(message)[:500]
