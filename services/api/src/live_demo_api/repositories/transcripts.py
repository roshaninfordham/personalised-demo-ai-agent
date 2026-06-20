"""Transcript repositories."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import TranscriptEvent


class TranscriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_events(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        limit: int,
        speaker: str | None = None,
        chunk_type: str | None = None,
        from_ms: int | None = None,
        to_ms: int | None = None,
        cursor_created_at: datetime | None = None,
        cursor_event_id: UUID | None = None,
    ) -> list[TranscriptEvent]:
        statement = select(TranscriptEvent).where(
            TranscriptEvent.organization_id == organization_id,
            TranscriptEvent.session_id == session_id,
        )
        if speaker is not None:
            statement = statement.where(TranscriptEvent.speaker == speaker)
        if chunk_type is not None:
            statement = statement.where(TranscriptEvent.chunk_type == chunk_type)
        if from_ms is not None:
            statement = statement.where(TranscriptEvent.start_ms >= from_ms)
        if to_ms is not None:
            statement = statement.where(TranscriptEvent.end_ms <= to_ms)
        if cursor_created_at is not None and cursor_event_id is not None:
            statement = statement.where(
                sa.or_(
                    TranscriptEvent.created_at > cursor_created_at,
                    sa.and_(
                        TranscriptEvent.created_at == cursor_created_at,
                        TranscriptEvent.transcript_event_id > cursor_event_id,
                    ),
                )
            )
        statement = statement.order_by(
            TranscriptEvent.created_at.asc(), TranscriptEvent.transcript_event_id.asc()
        ).limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def user_question_events(
        self, *, organization_id: UUID, session_id: UUID, limit: int
    ) -> list[TranscriptEvent]:
        statement = (
            select(TranscriptEvent)
            .where(
                TranscriptEvent.organization_id == organization_id,
                TranscriptEvent.session_id == session_id,
                TranscriptEvent.speaker == "user",
                TranscriptEvent.chunk_type == "final",
                TranscriptEvent.text.like("%?"),
            )
            .order_by(TranscriptEvent.created_at.asc(), TranscriptEvent.transcript_event_id.asc())
            .limit(limit)
        )
        return list((await self._session.scalars(statement)).all())
