"""Assistant interruption processor."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from live_demo_agent_runtime.events import event_types
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.transcripts.spoken_text_tracker import estimate_spoken_text
from live_demo_agent_runtime.transcripts.transcript_buffer import (
    TranscriptBuffer,
    TranscriptWriteItem,
)
from live_demo_agent_runtime.transcripts.transcript_sink import TranscriptSink
from live_demo_agent_runtime.tts.base import TextToSpeechProvider
from live_demo_agent_runtime.vad.interruption_state import InterruptionState


async def handle_interruption(
    *,
    state: InterruptionState,
    user_speech_duration_ms: int,
    threshold_ms: int,
    tts_provider: TextToSpeechProvider,
    transcript_sink: TranscriptSink,
    event_publisher: EventPublisher,
    organization_id: UUID,
    demo_session_id: UUID,
    voice_session_id: UUID,
    transcript_buffer: TranscriptBuffer,
    trace_id: str,
) -> bool:
    if not state.should_interrupt(user_speech_duration_ms, threshold_ms):
        return False
    await tts_provider.stop(voice_session_id)
    state.interrupt(now_ms=0)
    spoken_text, _estimated = estimate_spoken_text(
        text=state.current_text,
        spoken_char_count=state.spoken_char_count_estimate,
        emitted_audio_duration_ms=None,
    )
    if spoken_text:
        item = TranscriptWriteItem(
            transcript_event_id=uuid4(),
            organization_id=organization_id,
            demo_session_id=demo_session_id,
            speaker="assistant",
            chunk_type="interrupted",
            text=spoken_text,
            is_final=False,
            start_ms=None,
            end_ms=None,
            confidence=None,
            turn_id=state.current_assistant_turn_id,
            created_at=datetime.now(UTC),
            persist=True,
            publish=True,
        )
        await transcript_sink.enqueue(transcript_buffer, item, trace_id=trace_id)
    await event_publisher.publish(
        organization_id=organization_id,
        demo_session_id=demo_session_id,
        event_type=event_types.AGENT_INTERRUPTED,
        trace_id=trace_id,
        payload={"voice_session_id": str(voice_session_id)},
    )
    return True
