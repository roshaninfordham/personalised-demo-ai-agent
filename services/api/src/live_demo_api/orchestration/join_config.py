"""Join-config sanitization."""

from __future__ import annotations

SECRET_KEYS = ("secret", "api_key", "token", "authorization", "cookie", "password")


def sanitize_join_config(join_config: dict[str, object]) -> dict[str, object]:
    return {
        key: _sanitize_value(value)
        for key, value in join_config.items()
        if not any(token in key.lower() for token in SECRET_KEYS)
    }


def _sanitize_value(value: object) -> object:
    if isinstance(value, dict):
        return sanitize_join_config({str(key): child for key, child in value.items()})
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value
