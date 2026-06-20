"""Lead insight, summary, and CRM payload read services."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.errors import NotFoundError
from live_demo_api.pagination import clamp_limit, decode_cursor, encode_cursor
from live_demo_api.repositories.demo_sessions import DemoSessionRepository
from live_demo_api.repositories.lead_summaries import LeadSummaryRepository
from live_demo_api.security import Principal
from live_demo_api.services.mappers import insight_to_response, lead_summary_to_response
from live_demo_contracts.lead_summary import (
    CrmPayloadResponse,
    LeadInsightsResponse,
    LeadSummaryResponse,
)


def _cursor_parts(cursor: str | None) -> tuple[datetime | None, UUID | None]:
    if cursor is None:
        return None, None
    decoded = decode_cursor(cursor, max_length=get_settings().max_cursor_length)
    if "created_at" not in decoded or "id" not in decoded:
        return None, None
    return datetime.fromisoformat(decoded["created_at"]), UUID(decoded["id"])


class LeadSummaryService:
    async def _ensure_session(
        self, db: AsyncSession, principal: Principal, session_id: UUID
    ) -> None:
        row = await DemoSessionRepository(db).get_session(
            organization_id=principal.organization_id,
            session_id=session_id,
        )
        if row is None:
            raise NotFoundError("Session not found.", code="session_not_found")

    async def list_insights(
        self,
        db: AsyncSession,
        principal: Principal,
        session_id: UUID,
        *,
        insight_type: str | None,
        min_confidence: float | None,
        limit: int | None,
        cursor: str | None,
    ) -> LeadInsightsResponse:
        await self._ensure_session(db, principal, session_id)
        page_limit = clamp_limit(
            limit, default=100, maximum=get_settings().max_transcript_page_limit
        )
        cursor_created_at, cursor_insight_id = _cursor_parts(cursor)
        rows = await LeadSummaryRepository(db).list_insights(
            organization_id=principal.organization_id,
            session_id=session_id,
            insight_type=insight_type,
            min_confidence=min_confidence,
            limit=page_limit + 1,
            cursor_created_at=cursor_created_at,
            cursor_insight_id=cursor_insight_id,
        )
        next_cursor = None
        if len(rows) > page_limit:
            last = rows[page_limit - 1]
            next_cursor = encode_cursor(
                {"created_at": last.created_at.isoformat(), "id": str(last.insight_id)}
            )
            rows = rows[:page_limit]
        return LeadInsightsResponse(
            items=[insight_to_response(row) for row in rows],
            next_cursor=next_cursor,
        )

    async def get_summary(
        self, db: AsyncSession, principal: Principal, session_id: UUID
    ) -> LeadSummaryResponse:
        await self._ensure_session(db, principal, session_id)
        row = await LeadSummaryRepository(db).get_summary(
            organization_id=principal.organization_id,
            session_id=session_id,
        )
        if row is None:
            raise NotFoundError("Lead summary not found.", code="lead_summary_not_found")
        return LeadSummaryResponse(lead_summary=lead_summary_to_response(row))

    async def get_crm_payload(
        self, db: AsyncSession, principal: Principal, session_id: UUID
    ) -> CrmPayloadResponse:
        summary = await self.get_summary(db, principal, session_id)
        return CrmPayloadResponse(crm_payload=summary.lead_summary.crm_payload)
