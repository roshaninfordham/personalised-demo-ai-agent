"""Feature shown persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import FeatureShown
from live_demo_api.post_demo.features.feature_types import FeatureCandidate


class FeatureShownRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert_many(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        product_id: UUID,
        features: tuple[FeatureCandidate, ...],
    ) -> list[FeatureShown]:
        rows: list[FeatureShown] = []
        for feature in features:
            now = datetime.now(UTC)
            statement = (
                insert(FeatureShown)
                .values(
                    organization_id=organization_id,
                    session_id=session_id,
                    product_id=product_id,
                    feature_key=feature.feature_key,
                    feature_label=feature.feature_label,
                    feature_category=feature.feature_category,
                    source_type=feature.source_type,
                    confidence=feature.confidence,
                    evidence_transcript_event_ids=list(feature.evidence_transcript_event_ids),
                    evidence_browser_action_ids=list(feature.evidence_browser_action_ids),
                    evidence_screen_ids=list(feature.evidence_screen_ids),
                    evidence_recipe_step_ids=list(feature.evidence_recipe_step_ids),
                    first_seen_at=now,
                    last_seen_at=now,
                    updated_at=now,
                )
                .on_conflict_do_update(
                    constraint="uq_features_shown_session_key",
                    set_={
                        "feature_label": feature.feature_label,
                        "feature_category": feature.feature_category,
                        "confidence": feature.confidence,
                        "evidence_transcript_event_ids": list(
                            feature.evidence_transcript_event_ids
                        ),
                        "evidence_browser_action_ids": list(feature.evidence_browser_action_ids),
                        "evidence_screen_ids": list(feature.evidence_screen_ids),
                        "evidence_recipe_step_ids": list(feature.evidence_recipe_step_ids),
                        "last_seen_at": now,
                        "updated_at": now,
                    },
                )
                .returning(FeatureShown)
            )
            rows.append((await self._db.scalars(statement)).one())
        return rows

    async def list_for_session(
        self, *, organization_id: UUID, session_id: UUID, limit: int = 100
    ) -> list[FeatureShown]:
        statement = (
            select(FeatureShown)
            .where(
                FeatureShown.organization_id == organization_id,
                FeatureShown.session_id == session_id,
            )
            .order_by(FeatureShown.confidence.desc(), FeatureShown.feature_label.asc())
            .limit(limit)
        )
        return list((await self._db.scalars(statement)).all())
