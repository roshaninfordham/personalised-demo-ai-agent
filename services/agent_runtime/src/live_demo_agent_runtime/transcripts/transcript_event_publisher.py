"""Transcript event publishing."""

from collections.abc import Sequence

from live_demo_agent_runtime.events import event_types
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.transcripts.transcript_buffer import TranscriptWriteItem

EVENT_TYPE_BY_CHUNK = {
    "partial": event_types.TRANSCRIPT_PARTIAL,
    "final": event_types.TRANSCRIPT_FINAL,
    "interrupted": event_types.TRANSCRIPT_INTERRUPTED,
}


class TranscriptEventPublisher:
    def __init__(self, event_publisher: EventPublisher) -> None:
        self._event_publisher = event_publisher

    async def publish_items(
        self,
        items: Sequence[TranscriptWriteItem],
        *,
        trace_id: str,
    ) -> None:
        for item in items:
            if not item.publish:
                continue
            await self._event_publisher.publish(
                organization_id=item.organization_id,
                demo_session_id=item.demo_session_id,
                event_type=EVENT_TYPE_BY_CHUNK[item.chunk_type],
                trace_id=trace_id,
                payload={
                    "transcript_event_id": str(item.transcript_event_id),
                    "session_id": str(item.demo_session_id),
                    "speaker": item.speaker,
                    "chunk_type": item.chunk_type,
                    "text": item.text,
                    "start_ms": item.start_ms,
                    "end_ms": item.end_ms,
                    "confidence": item.confidence,
                    "turn_id": str(item.turn_id) if item.turn_id else None,
                },
            )
