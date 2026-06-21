from datetime import UTC, datetime
from typing import cast
from uuid import UUID, uuid4

from live_demo_agent_runtime.events.redis_event_publisher import InMemoryEventPublisher
from live_demo_agent_runtime.transcripts.transcript_buffer import (
    TranscriptBuffer,
    TranscriptChunkType,
    TranscriptWriteItem,
)
from live_demo_agent_runtime.transcripts.transcript_event_publisher import TranscriptEventPublisher
from live_demo_agent_runtime.transcripts.transcript_repository import TranscriptRepository
from live_demo_agent_runtime.transcripts.transcript_sink import TranscriptSink


def _item(demo_session_id: UUID, *, chunk_type: str, persist: bool) -> TranscriptWriteItem:
    return TranscriptWriteItem(
        transcript_event_id=uuid4(),
        organization_id=uuid4(),
        demo_session_id=demo_session_id,
        speaker="user",
        chunk_type=cast(TranscriptChunkType, chunk_type),
        text="hello",
        is_final=chunk_type == "final",
        start_ms=None,
        end_ms=None,
        confidence=0.9,
        turn_id=uuid4(),
        created_at=datetime.now(UTC),
        persist=persist,
        publish=True,
    )


async def test_partial_publishes_but_does_not_persist_by_default() -> None:
    event_publisher = InMemoryEventPublisher()
    sink = TranscriptSink(
        sessionmaker=None,
        repository=TranscriptRepository(),
        publisher=TranscriptEventPublisher(event_publisher),
    )
    buffer = TranscriptBuffer()
    await sink.enqueue(
        buffer,
        _item(uuid4(), chunk_type="partial", persist=False),
        trace_id="trace",
    )
    assert len(event_publisher.events) == 1
    assert buffer.snapshot()[0].persist is False


async def test_final_publishes_and_marks_persist() -> None:
    event_publisher = InMemoryEventPublisher()
    sink = TranscriptSink(
        sessionmaker=None,
        repository=TranscriptRepository(),
        publisher=TranscriptEventPublisher(event_publisher),
    )
    buffer = TranscriptBuffer()
    item = _item(uuid4(), chunk_type="final", persist=True)
    await sink.enqueue(buffer, item, trace_id="trace")
    assert len(event_publisher.events) == 1
    assert buffer.snapshot()[0].persist is True
