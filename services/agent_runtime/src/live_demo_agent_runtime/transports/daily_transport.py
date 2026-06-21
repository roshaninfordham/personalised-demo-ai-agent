"""Optional Daily managed WebRTC transport skeleton."""

from datetime import datetime
from typing import Any
from uuid import UUID

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.transports.join_config import VoiceJoinConfig


class DailyTransportProvider:
    provider_name = "daily"

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
        if self._settings.daily_api_key is None:
            raise ProviderCapabilityError("daily", "Daily transport is not configured.")
        self._sessions[voice_session_id] = VoiceJoinConfig(
            transport_provider=self.provider_name,
            voice_session_id=voice_session_id,
            room_url=self._settings.daily_room_url,
            expires_at=expires_at,
            status="not_implemented_in_phase_7",
            offer_required=False,
        )

    async def get_join_config(self, voice_session_id: UUID) -> VoiceJoinConfig:
        return self._sessions[voice_session_id]

    async def build_pipecat_transport(self, voice_session: object) -> Any:
        del voice_session
        raise ProviderCapabilityError(
            "daily",
            "Daily Pipecat transport is not implemented in Phase 7.",
        )

    async def close(self, voice_session_id: UUID) -> None:
        self._sessions.pop(voice_session_id, None)
