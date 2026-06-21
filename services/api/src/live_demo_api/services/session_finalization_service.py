"""Phase 12 deterministic session finalization."""

from __future__ import annotations

from uuid import UUID

from live_demo_api.orchestration.orchestration_shutdown import deterministic_summary_payload


class SessionFinalizationService:
    async def deterministic_summary(self, session_id: UUID) -> dict[str, object]:
        return deterministic_summary_payload(session_id=session_id)
