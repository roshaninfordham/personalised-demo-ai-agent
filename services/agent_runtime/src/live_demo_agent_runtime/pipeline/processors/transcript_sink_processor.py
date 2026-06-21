"""Map known transcript chunks into transcript sink items."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from live_demo_agent_runtime.stt.transcript_types import TranscriptChunk
from live_demo_agent_runtime.transcripts.transcript_buffer import (
    TranscriptChunkType,
    TranscriptSpeaker,
    TranscriptWriteItem,
)


def transcript_chunk_to_write_item(
    *,
    chunk: TranscriptChunk,
    organization_id: UUID,
    demo_session_id: UUID,
    speaker: TranscriptSpeaker,
    turn_id: UUID,
    persist_partials: bool,
    persist_finals: bool,
) -> TranscriptWriteItem:
    chunk_type: TranscriptChunkType = "final" if chunk.is_final else "partial"
    return TranscriptWriteItem(
        transcript_event_id=uuid4(),
        organization_id=organization_id,
        demo_session_id=demo_session_id,
        speaker=speaker,
        chunk_type=chunk_type,
        text=chunk.text,
        is_final=chunk.is_final,
        start_ms=chunk.start_ms,
        end_ms=chunk.end_ms,
        confidence=chunk.confidence,
        turn_id=turn_id,
        created_at=datetime.now(UTC),
        persist=persist_finals if chunk.is_final else persist_partials,
        publish=True,
    )
