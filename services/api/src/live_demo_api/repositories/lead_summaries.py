"""Lead insight and summary repositories."""

from datetime import datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import LeadInsight, LeadSummary


class LeadSummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_insights(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        limit: int,
        insight_type: str | None = None,
        min_confidence: float | None = None,
        cursor_created_at: datetime | None = None,
        cursor_insight_id: UUID | None = None,
    ) -> list[LeadInsight]:
        statement = select(LeadInsight).where(
            LeadInsight.organization_id == organization_id,
            LeadInsight.session_id == session_id,
        )
        if insight_type is not None:
            statement = statement.where(LeadInsight.insight_type == insight_type)
        if min_confidence is not None:
            statement = statement.where(LeadInsight.confidence >= min_confidence)
        if cursor_created_at is not None and cursor_insight_id is not None:
            statement = statement.where(
                sa.or_(
                    LeadInsight.created_at < cursor_created_at,
                    sa.and_(
                        LeadInsight.created_at == cursor_created_at,
                        LeadInsight.insight_id < cursor_insight_id,
                    ),
                )
            )
        statement = statement.order_by(
            LeadInsight.created_at.desc(), LeadInsight.insight_id.desc()
        ).limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def get_summary(self, *, organization_id: UUID, session_id: UUID) -> LeadSummary | None:
        statement = select(LeadSummary).where(
            LeadSummary.organization_id == organization_id,
            LeadSummary.session_id == session_id,
        )
        return cast(LeadSummary | None, await self._session.scalar(statement))
