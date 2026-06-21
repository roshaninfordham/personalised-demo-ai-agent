"""Postgres transcript persistence."""

from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_agent_runtime.transcripts.transcript_buffer import TranscriptWriteItem


class TranscriptRepository:
    async def insert_transcript_events(
        self,
        session: AsyncSession,
        items: Sequence[TranscriptWriteItem],
    ) -> None:
        rows = [
            {
                "transcript_event_id": item.transcript_event_id,
                "organization_id": item.organization_id,
                "session_id": item.demo_session_id,
                "speaker": item.speaker,
                "chunk_type": item.chunk_type,
                "text": item.text,
                "is_final": item.is_final,
                "start_ms": item.start_ms,
                "end_ms": item.end_ms,
                "confidence": item.confidence,
                "turn_id": item.turn_id,
                "created_at": item.created_at,
            }
            for item in items
            if item.persist
        ]
        if not rows:
            return
        await session.execute(
            text(
                """
                insert into transcript_events (
                    transcript_event_id,
                    organization_id,
                    session_id,
                    speaker,
                    chunk_type,
                    text,
                    is_final,
                    start_ms,
                    end_ms,
                    confidence,
                    turn_id,
                    created_at
                )
                values (
                    :transcript_event_id,
                    :organization_id,
                    :session_id,
                    :speaker,
                    :chunk_type,
                    :text,
                    :is_final,
                    :start_ms,
                    :end_ms,
                    :confidence,
                    :turn_id,
                    :created_at
                )
                on conflict (transcript_event_id) do nothing
                """
            ),
            rows,
        )
