from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from live_demo_agent_runtime.transcripts.transcript_buffer import (
    TranscriptBuffer,
    TranscriptChunkType,
    TranscriptWriteItem,
)


def _item(chunk_type: str, persist: bool = False) -> TranscriptWriteItem:
    return TranscriptWriteItem(
        transcript_event_id=uuid4(),
        organization_id=uuid4(),
        demo_session_id=uuid4(),
        speaker="user",
        chunk_type=cast(TranscriptChunkType, chunk_type),
        text=chunk_type,
        is_final=chunk_type == "final",
        start_ms=None,
        end_ms=None,
        confidence=None,
        turn_id=uuid4(),
        created_at=datetime.now(UTC),
        persist=persist,
        publish=True,
    )


def test_transcript_buffer_drops_partials_before_finals() -> None:
    buffer = TranscriptBuffer(max_items=2)
    buffer.append(_item("partial"))
    final = _item("final", persist=True)
    buffer.append(final)
    buffer.append(_item("partial"))
    assert final in buffer.snapshot()
    assert buffer.partial_dropped_count == 1


def test_drain_batch_returns_items() -> None:
    buffer = TranscriptBuffer(max_items=2)
    buffer.append(_item("final"))
    assert len(buffer.drain_batch()) == 1
    assert buffer.length == 0
