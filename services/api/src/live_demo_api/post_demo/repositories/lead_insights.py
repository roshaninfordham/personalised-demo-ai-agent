"""Lead insight persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import LeadInsight
from live_demo_api.post_demo.insights.insight_types import (
    ExtractedLeadInsight,
    normalized_content_hash,
)


class LeadInsightPostDemoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert_many(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        insights: tuple[ExtractedLeadInsight, ...],
    ) -> list[LeadInsight]:
        rows: list[LeadInsight] = []
        for insight in insights:
            content_hash = normalized_content_hash(
                session_id, insight.insight_type, insight.normalized_content
            )
            statement = (
                insert(LeadInsight)
                .values(
                    organization_id=organization_id,
                    session_id=session_id,
                    insight_type=insight.insight_type,
                    content=insight.content,
                    normalized_content_hash=content_hash,
                    confidence=insight.confidence,
                    importance=insight.importance,
                    evidence_transcript_event_ids=list(insight.evidence_transcript_event_ids),
                    evidence_browser_action_ids=list(insight.evidence_browser_action_ids),
                    evidence_screen_ids=list(insight.evidence_screen_ids),
                    evidence_recipe_step_ids=list(insight.evidence_recipe_step_ids),
                    source=insight.extraction_method,
                    updated_at=datetime.now(UTC),
                )
                .on_conflict_do_update(
                    index_elements=[
                        LeadInsight.session_id,
                        LeadInsight.insight_type,
                        LeadInsight.normalized_content_hash,
                    ],
                    index_where=text("normalized_content_hash <> ''"),
                    set_={
                        "confidence": insight.confidence,
                        "importance": insight.importance,
                        "evidence_transcript_event_ids": list(
                            insight.evidence_transcript_event_ids
                        ),
                        "evidence_browser_action_ids": list(insight.evidence_browser_action_ids),
                        "evidence_screen_ids": list(insight.evidence_screen_ids),
                        "evidence_recipe_step_ids": list(insight.evidence_recipe_step_ids),
                        "updated_at": datetime.now(UTC),
                    },
                )
                .returning(LeadInsight)
            )
            rows.append((await self._db.scalars(statement)).one())
        return rows
