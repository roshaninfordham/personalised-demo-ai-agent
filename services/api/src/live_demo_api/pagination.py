"""Deterministic keyset pagination helpers."""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping

from live_demo_api.errors import ValidationAppError


def encode_cursor(payload: Mapping[str, str]) -> str:
    encoded = json.dumps(dict(sorted(payload.items())), separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(encoded).decode("ascii").rstrip("=")


def decode_cursor(cursor: str, *, max_length: int = 2048) -> dict[str, str]:
    if len(cursor) > max_length:
        raise ValidationAppError("Invalid pagination cursor.", code="invalid_cursor")
    padding = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode((cursor + padding).encode("ascii"))
        parsed = json.loads(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValidationAppError("Invalid pagination cursor.", code="invalid_cursor") from exc
    if not isinstance(parsed, dict) or not all(
        isinstance(key, str) and isinstance(value, str) for key, value in parsed.items()
    ):
        raise ValidationAppError("Invalid pagination cursor.", code="invalid_cursor")
    allowed_keys = {"created_at", "id"}
    if set(parsed) - allowed_keys:
        raise ValidationAppError("Invalid pagination cursor.", code="invalid_cursor")
    return parsed


def clamp_limit(limit: int | None, *, default: int, maximum: int) -> int:
    if limit is None:
        return default
    if limit < 1:
        raise ValidationAppError("Limit must be positive.", code="invalid_limit")
    return min(limit, maximum)
