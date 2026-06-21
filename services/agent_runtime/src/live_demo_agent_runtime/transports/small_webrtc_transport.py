"""SmallWebRTC local transport adapter.

Pipecat-specific imports are intentionally isolated here and in pipecat_adapters.
The installed CI environment may not include Pipecat, so this adapter provides the
safe local join config and leaves concrete transport construction to the adapter.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.transports.join_config import VoiceJoinConfig


class SmallWebRTCTransportProvider:
    provider_name = "small_webrtc"

    def __init__(self, settings: AgentRuntimeSettings) -> None:
        self._settings = settings
        self._sessions: dict[UUID, VoiceJoinConfig] = {}

    async def create_session(
        self,
        *,
        voice_session_id: UUID,
        organization_id: UUID,
        demo_session_id: UUID,
        product_id: UUID,
        expires_at: datetime,
    ) -> None:
        del organization_id, demo_session_id, product_id
        self._sessions[voice_session_id] = VoiceJoinConfig(
            transport_provider=self.provider_name,
            voice_session_id=voice_session_id,
            signaling_url=(
                f"http://localhost:{self._settings.agent_runtime_port}"
                f"/internal/agent/v1/voice-sessions/{voice_session_id}/small-webrtc"
            ),
            ice_servers=[],
            expires_at=expires_at,
            status="ready_for_signaling",
            offer_required=True,
        )

    async def get_join_config(self, voice_session_id: UUID) -> VoiceJoinConfig:
        return self._sessions[voice_session_id]

    async def build_pipecat_transport(self, voice_session: object) -> Any:
        del voice_session
        return None

    async def close(self, voice_session_id: UUID) -> None:
        self._sessions.pop(voice_session_id, None)
