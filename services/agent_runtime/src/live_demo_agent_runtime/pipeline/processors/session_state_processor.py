"""Small helpers for session status payloads."""

from live_demo_agent_runtime.sessions.voice_session import VoiceSession


def voice_session_payload(session: VoiceSession) -> dict[str, object]:
    return {
        "voice_session_id": str(session.voice_session_id),
        "demo_session_id": str(session.demo_session_id),
        "product_id": str(session.product_id),
        "transport_provider": session.transport_provider,
        "status": session.status.value,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "expires_at": session.expires_at.isoformat(),
    }
