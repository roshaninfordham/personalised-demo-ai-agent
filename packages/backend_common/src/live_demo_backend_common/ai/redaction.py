from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

SENSITIVE_KEY_PATTERNS = [
    "api_key",
    "authorization",
    "bearer",
    "token",
    "secret",
    "password",
    "client_secret",
    "refresh_token",
    "access_token",
    "cookie",
]


def is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return any(pattern in normalized for pattern in SENSITIVE_KEY_PATTERNS)


def redact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, item in value.items():
        if is_sensitive_key(str(key)):
            redacted[str(key)] = "***REDACTED***"
        elif isinstance(item, Mapping):
            redacted[str(key)] = redact_mapping(item)
        elif isinstance(item, list):
            redacted[str(key)] = [
                redact_mapping(child) if isinstance(child, Mapping) else child for child in item
            ]
        else:
            redacted[str(key)] = item
    return redacted


def safe_hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_hash_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return safe_hash_text(payload)
