"""Provider-agnostic join-config placeholder service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from live_demo_api.config import get_settings
from live_demo_contracts.demo_session import JoinConfigResponse


class JoinConfigService:
    async def get_join_config(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
    ) -> JoinConfigResponse:
        _ = organization_id
        settings = get_settings()
        expires_at = datetime.now(UTC) + timedelta(seconds=settings.transport_room_ttl_seconds)
        return JoinConfigResponse(
            transport_provider=settings.transport_provider,
            session_id=str(session_id),
            room_id="local-placeholder",
            join_token=None,
            expires_at=expires_at.isoformat(),
            status="not_implemented_in_phase_3",
        )
