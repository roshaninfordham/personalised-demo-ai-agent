"""Bounded tenant-scoped evidence loader."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import (
    ActionEvent,
    DemoSession,
    LeadInsight,
    RecipeStepProgress,
    ScreenSnapshot,
    TranscriptEvent,
)
from live_demo_api.errors import NotFoundError
from live_demo_api.post_demo.evidence.evidence_types import (
    ActionEvidence,
    EvidenceLoadRequest,
    LeadInsightEvidence,
    RecipeStepEvidence,
    ScreenEvidence,
    SessionEvidenceBundle,
    TranscriptEvidence,
)
from live_demo_api.services.mappers import as_float


class EvidenceLoader:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def load(self, request: EvidenceLoadRequest) -> SessionEvidenceBundle:
        session = await self._db.scalar(
            select(DemoSession).where(
                DemoSession.organization_id == request.organization_id,
                DemoSession.session_id == request.session_id,
            )
        )
        if session is None:
            raise NotFoundError("Session not found.", code="session_not_found")

        transcripts = list(
            (
                await self._db.scalars(
                    select(TranscriptEvent)
                    .where(
                        TranscriptEvent.organization_id == request.organization_id,
                        TranscriptEvent.session_id == request.session_id,
                    )
                    .order_by(
                        TranscriptEvent.created_at.asc(),
                        TranscriptEvent.transcript_event_id.asc(),
                    )
                    .limit(request.max_transcript_events)
                )
            ).all()
        )
        actions = list(
            (
                await self._db.scalars(
                    select(ActionEvent)
                    .where(
                        ActionEvent.organization_id == request.organization_id,
                        ActionEvent.session_id == request.session_id,
                    )
                    .order_by(ActionEvent.created_at.asc(), ActionEvent.action_event_id.asc())
                    .limit(request.max_action_events)
                )
            ).all()
        )
        screen_ids = {
            screen_id
            for action in actions
            for screen_id in (action.from_screen_id, action.to_screen_id)
            if screen_id is not None
        }
        if screen_ids:
            screen_filter = or_(
                ScreenSnapshot.session_id == request.session_id,
                ScreenSnapshot.screen_id.in_(screen_ids),
            )
        else:
            screen_filter = ScreenSnapshot.session_id == request.session_id
        screen_statement = (
            select(ScreenSnapshot)
            .where(
                ScreenSnapshot.organization_id == request.organization_id,
                ScreenSnapshot.product_id == session.product_id,
                screen_filter,
            )
            .order_by(ScreenSnapshot.created_at.asc(), ScreenSnapshot.screen_id.asc())
            .limit(request.max_screen_events)
        )
        screens = list((await self._db.scalars(screen_statement)).all())
        progress_rows = list(
            (
                await self._db.scalars(
                    select(RecipeStepProgress)
                    .where(
                        RecipeStepProgress.organization_id == request.organization_id,
                        RecipeStepProgress.session_id == request.session_id,
                    )
                    .order_by(RecipeStepProgress.created_at.asc())
                )
            ).all()
        )
        insights = list(
            (
                await self._db.scalars(
                    select(LeadInsight)
                    .where(
                        LeadInsight.organization_id == request.organization_id,
                        LeadInsight.session_id == request.session_id,
                    )
                    .order_by(LeadInsight.created_at.asc(), LeadInsight.insight_id.asc())
                )
            ).all()
        )

        return SessionEvidenceBundle(
            organization_id=request.organization_id,
            session_id=request.session_id,
            product_id=session.product_id,
            transcript_events=tuple(
                TranscriptEvidence(
                    transcript_event_id=row.transcript_event_id,
                    speaker=row.speaker,
                    chunk_type=row.chunk_type,
                    text=row.text,
                    is_final=row.is_final,
                    turn_id=row.turn_id,
                    created_at=row.created_at,
                )
                for row in transcripts
            ),
            action_events=tuple(
                ActionEvidence(
                    action_event_id=row.action_event_id,
                    action_type=row.action_type,
                    action_payload=row.action_payload,
                    risk_level=row.risk_level,
                    policy_decision=row.policy_decision,
                    success=row.success,
                    from_screen_id=row.from_screen_id,
                    to_screen_id=row.to_screen_id,
                    created_at=row.created_at,
                )
                for row in actions
            ),
            screen_events=tuple(
                ScreenEvidence(
                    screen_id=row.screen_id,
                    screen_hash=row.screen_hash,
                    url=row.url,
                    title=row.title,
                    summary=row.summary,
                    created_at=row.created_at,
                )
                for row in screens
            ),
            recipe_progress=tuple(
                RecipeStepEvidence(
                    recipe_step_progress_id=row.recipe_step_progress_id,
                    recipe_id=row.recipe_id,
                    step_id=row.step_id,
                    step_key=row.step_key,
                    status=row.status,
                    matched_screen_id=row.matched_screen_id,
                    matched_action_id=row.matched_action_id,
                    matched_confidence=as_float(row.matched_confidence),
                    evidence=row.evidence,
                    updated_at=row.updated_at,
                )
                for row in progress_rows
            ),
            existing_insights=tuple(
                LeadInsightEvidence(
                    insight_id=row.insight_id,
                    insight_type=row.insight_type,
                    content=row.content,
                    confidence=as_float(row.confidence),
                    evidence_transcript_event_ids=tuple(row.evidence_transcript_event_ids),
                    evidence_browser_action_ids=tuple(row.evidence_browser_action_ids),
                    evidence_screen_ids=tuple(row.evidence_screen_ids),
                    evidence_recipe_step_ids=tuple(getattr(row, "evidence_recipe_step_ids", ())),
                    created_at=row.created_at,
                )
                for row in insights
            ),
            loaded_at=datetime.now(UTC),
        )
