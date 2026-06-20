"""Centralized Redis key builders for live-state and stream data."""

from uuid import UUID

from live_demo_api.config import get_settings


def _prefix() -> str:
    configured = get_settings().redis_key_prefix.strip()
    if not configured:
        raise ValueError("REDIS_KEY_PREFIX must not be empty")
    return configured


def _segment(value: UUID | str) -> str:
    raw = str(value).strip()
    if not raw:
        raise ValueError("Redis key segment must not be empty")
    if ":" in raw or "/" in raw or raw.startswith(".") or raw.endswith("."):
        raise ValueError("Redis key segment contains an unsafe character")
    return raw


def session_state_key(session_id: UUID | str) -> str:
    return f"{_prefix()}:session:{_segment(session_id)}:state"


def current_screen_key(session_id: UUID | str) -> str:
    return f"{_prefix()}:session:{_segment(session_id)}:current_screen"


def safe_actions_key(session_id: UUID | str) -> str:
    return f"{_prefix()}:session:{_segment(session_id)}:safe_actions"


def transcript_window_key(session_id: UUID | str) -> str:
    return f"{_prefix()}:session:{_segment(session_id)}:transcript_window"


def latency_key(session_id: UUID | str) -> str:
    return f"{_prefix()}:session:{_segment(session_id)}:latency"


def browser_status_key(session_id: UUID | str) -> str:
    return f"{_prefix()}:session:{_segment(session_id)}:browser_status"


def session_lock_key(session_id: UUID | str) -> str:
    return f"{_prefix()}:session:{_segment(session_id)}:lock"


def browser_state_key(browser_session_id: UUID | str) -> str:
    return f"{_prefix()}:browser:{_segment(browser_session_id)}:state"


def browser_screen_key(browser_session_id: UUID | str) -> str:
    return f"{_prefix()}:browser:{_segment(browser_session_id)}:screen"


def browser_lock_key(browser_session_id: UUID | str) -> str:
    return f"{_prefix()}:browser:{_segment(browser_session_id)}:lock"


def session_events_stream_key(session_id: UUID | str) -> str:
    return f"{_prefix()}:stream:session:{_segment(session_id)}:events"


def global_events_stream_key() -> str:
    return f"{_prefix()}:stream:global:events"


def dead_letter_stream_key() -> str:
    return f"{_prefix()}:stream:dead_letter"


def processed_event_key(consumer_name: str, event_id: UUID | str) -> str:
    return f"{_prefix()}:processed:{_segment(consumer_name)}:{_segment(event_id)}"
