"""Custom transport placeholder."""

from datetime import datetime
from typing import Any
from uuid import UUID

from live_demo_agent_runtime.errors import ProviderCapabilityError
from live_demo_agent_runtime.transports.join_config import VoiceJoinConfig


class CustomTransportProvider:
    provider_name = "custom"

    async def create_session(
        self,
        *,
        voice_session_id: UUID,
        organization_id: UUID,
        demo_session_id: UUID,
        product_id: UUID,
        expires_at: datetime,
    ) -> None:
        del voice_session_id, organization_id, demo_session_id, product_id, expires_at
        raise ProviderCapabilityError("custom", "Custom transport is not configured.")

    async def get_join_config(self, voice_session_id: UUID) -> VoiceJoinConfig:
        del voice_session_id
        raise ProviderCapabilityError("custom", "Custom transport is not configured.")

    async def build_pipecat_transport(self, voice_session: object) -> Any:
        del voice_session
        raise ProviderCapabilityError("custom", "Custom transport is not configured.")

    async def close(self, voice_session_id: UUID) -> None:
        del voice_session_id
