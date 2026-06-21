"""Provider-agnostic realtime voice transport interface."""

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from live_demo_agent_runtime.transports.join_config import VoiceJoinConfig


class RealtimeVoiceTransport(Protocol):
    provider_name: str

    async def create_session(
        self,
        *,
        voice_session_id: UUID,
        organization_id: UUID,
        demo_session_id: UUID,
        product_id: UUID,
        expires_at: datetime,
    ) -> None: ...

    async def get_join_config(self, voice_session_id: UUID) -> VoiceJoinConfig: ...

    async def build_pipecat_transport(self, voice_session: object) -> Any: ...

    async def close(self, voice_session_id: UUID) -> None: ...
