from uuid import uuid4

import pytest

from live_demo_api.live_state.redis_keys import (
    browser_lock_key,
    current_screen_key,
    dead_letter_stream_key,
    global_events_stream_key,
    latency_key,
    safe_actions_key,
    session_events_stream_key,
    session_lock_key,
    session_state_key,
    transcript_window_key,
)


def test_session_key_builders_are_namespaced() -> None:
    session_id = uuid4()
    assert session_state_key(session_id) == f"live_demo:session:{session_id}:state"
    assert current_screen_key(session_id).endswith(":current_screen")
    assert safe_actions_key(session_id).endswith(":safe_actions")
    assert transcript_window_key(session_id).endswith(":transcript_window")
    assert latency_key(session_id).endswith(":latency")
    assert session_lock_key(session_id).endswith(":lock")
    assert session_events_stream_key(session_id).endswith(":events")
    assert global_events_stream_key() == "live_demo:stream:global:events"
    assert dead_letter_stream_key() == "live_demo:stream:dead_letter"


def test_key_builders_reject_unsafe_segments() -> None:
    with pytest.raises(ValueError):
        session_state_key("")
    with pytest.raises(ValueError):
        browser_lock_key("abc:def")
