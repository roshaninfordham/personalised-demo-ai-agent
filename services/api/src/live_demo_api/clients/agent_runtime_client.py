"""Agent runtime client abstraction for orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid5

import httpx

from live_demo_api.config import get_settings


@dataclass(frozen=True, slots=True)
class VoiceSessionResult:
    voice_session_id: UUID
    transport_session_id: str
    join_config: dict[str, object]


class AgentRuntimeClient:
    async def create_voice_session(
        self, *, organization_id: UUID, product_id: UUID, session_id: UUID, trace_id: str
    ) -> VoiceSessionResult:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
                response = await client.post(
                    f"{settings.agent_runtime_base_url}/internal/agent/v1/voice-sessions",
                    json={
                        "organization_id": str(organization_id),
                        "demo_session_id": str(session_id),
                        "product_id": str(product_id),
                        "transport_provider": settings.transport_provider,
                        "trace_id": trace_id,
                    },
                    headers={"X-Trace-ID": trace_id},
                )
                response.raise_for_status()
                payload = response.json()
                join_config = dict(payload.get("join_config") or {})
                voice_session_id = UUID(str(payload["voice_session_id"]))
                transport_session_id = str(
                    join_config.get("room_name")
                    or join_config.get("transport_session_id")
                    or f"transport-{session_id}"
                )
                return VoiceSessionResult(
                    voice_session_id=voice_session_id,
                    transport_session_id=transport_session_id,
                    join_config=_phase12_join_config(session_id, voice_session_id, join_config),
                )
        except (httpx.HTTPError, KeyError, ValueError):
            pass
        _ = organization_id, product_id, trace_id
        voice_session_id = uuid5(session_id, "voice-session")
        transport_session_id = f"transport-{session_id}"
        expires_at = datetime.now(UTC) + timedelta(seconds=settings.transport_room_ttl_seconds)
        return VoiceSessionResult(
            voice_session_id=voice_session_id,
            transport_session_id=transport_session_id,
            join_config={
                "session_id": str(session_id),
                "voice_session_id": str(voice_session_id),
                "transport_provider": settings.transport_provider,
                "status": "ready_for_signaling",
                "expires_at": expires_at.isoformat(),
                "join": {
                    "signaling_url": f"/internal/webrtc/{voice_session_id}",
                    "ice_servers": [],
                },
                "capabilities": {"audio": True, "video": False, "screenshare": False},
            },
        )

    async def send_greeting(
        self, *, voice_session_id: UUID, greeting_text: str, trace_id: str
    ) -> bool:
        _ = voice_session_id, greeting_text, trace_id
        return True

    async def stop_voice_session(self, *, voice_session_id: UUID, trace_id: str) -> bool:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
                response = await client.post(
                    f"{settings.agent_runtime_base_url}/internal/agent/v1/voice-sessions/"
                    f"{voice_session_id}/stop",
                    headers={"X-Trace-ID": trace_id},
                )
                return response.status_code < 500
        except httpx.HTTPError:
            pass
        _ = voice_session_id, trace_id
        return True

    async def flush_transcripts(self, *, voice_session_id: UUID, trace_id: str) -> bool:
        _ = voice_session_id, trace_id
        return True


def _phase12_join_config(
    session_id: UUID, voice_session_id: UUID, raw_join_config: dict[str, object]
) -> dict[str, object]:
    expires_at = raw_join_config.get("expires_at")
    if not isinstance(expires_at, str):
        expires_at = (datetime.now(UTC) + timedelta(seconds=600)).isoformat()
    signaling_url = raw_join_config.get("signaling_url") or raw_join_config.get("join_url") or ""
    return {
        "session_id": str(session_id),
        "voice_session_id": str(voice_session_id),
        "transport_provider": str(
            raw_join_config.get("provider") or get_settings().transport_provider
        ),
        "status": "ready_for_signaling",
        "expires_at": expires_at,
        "join": {"signaling_url": str(signaling_url), "ice_servers": []},
        "capabilities": {"audio": True, "video": False, "screenshare": False},
    }


def _timeout_seconds() -> float:
    return get_settings().internal_service_timeout_ms / 1000
