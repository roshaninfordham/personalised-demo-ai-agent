"""Lead summary persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import LeadSummary


class LeadSummaryPostDemoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert_summary(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        summary: dict[str, Any],
        confidence: float,
        evidence_summary: dict[str, Any],
        redaction_applied: bool,
        generation_mode: str,
    ) -> LeadSummary:
        statement = (
            insert(LeadSummary)
            .values(
                organization_id=organization_id,
                session_id=session_id,
                summary=summary,
                confidence=confidence,
                evidence_summary=evidence_summary,
                redaction_applied=redaction_applied,
                generation_mode=generation_mode,
                updated_at=datetime.now(UTC),
            )
            .on_conflict_do_update(
                constraint="uq_lead_summaries_session_id",
                set_={
                    "summary": summary,
                    "confidence": confidence,
                    "evidence_summary": evidence_summary,
                    "redaction_applied": redaction_applied,
                    "generation_mode": generation_mode,
                    "updated_at": datetime.now(UTC),
                },
            )
            .returning(LeadSummary)
        )
        return (await self._db.scalars(statement)).one()
