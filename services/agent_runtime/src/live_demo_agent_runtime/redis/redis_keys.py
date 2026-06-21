"""Centralized Redis key builders."""


def stream_key(prefix: str, demo_session_id: str) -> str:
    return f"{prefix}:stream:session:{demo_session_id}:events"


def global_stream_key(prefix: str) -> str:
    return f"{prefix}:stream:global:events"


def voice_status_key(prefix: str, demo_session_id: str) -> str:
    return f"{prefix}:session:{demo_session_id}:voice_status"
