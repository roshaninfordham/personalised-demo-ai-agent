import pytest

from live_demo_api.errors import ValidationAppError
from live_demo_api.pagination import clamp_limit, decode_cursor, encode_cursor


def test_cursor_round_trip_is_deterministic() -> None:
    cursor = encode_cursor({"created_at": "2026-06-20T12:00:00+00:00", "id": "abc"})
    assert decode_cursor(cursor) == {"created_at": "2026-06-20T12:00:00+00:00", "id": "abc"}


def test_invalid_cursor_is_rejected() -> None:
    with pytest.raises(ValidationAppError):
        decode_cursor("***not-base64***")


def test_clamp_limit_uses_bounds() -> None:
    assert clamp_limit(None, default=25, maximum=100) == 25
    assert clamp_limit(500, default=25, maximum=100) == 100
