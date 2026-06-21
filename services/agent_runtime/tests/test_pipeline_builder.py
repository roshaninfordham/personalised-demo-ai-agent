import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from live_demo_agent_runtime.events.redis_event_publisher import InMemoryEventPublisher
from live_demo_agent_runtime.pipecat_adapters.pipeline_builder import run_fake_voice_turn
from live_demo_agent_runtime.sessions.session_state import VoiceSessionStatus
from live_demo_agent_runtime.sessions.voice_session import VoiceSession
from live_demo_agent_runtime.stt.fake import FakeSpeechToTextProvider
from live_demo_agent_runtime.transcripts.transcript_buffer import TranscriptBuffer
from live_demo_agent_runtime.transcripts.transcript_event_publisher import TranscriptEventPublisher
from live_demo_agent_runtime.transcripts.transcript_repository import TranscriptRepository
from live_demo_agent_runtime.transcripts.transcript_sink import TranscriptSink
from live_demo_agent_runtime.tts.fake import FakeTextToSpeechProvider
from live_demo_agent_runtime.vad.interruption_state import InterruptionState

from .helpers import test_settings


def _voice_session() -> VoiceSession:
    now = datetime.now(UTC)
    return VoiceSession(
        voice_session_id=uuid4(),
        organization_id=uuid4(),
        demo_session_id=uuid4(),
        product_id=uuid4(),
        transport_provider="small_webrtc",
        status=VoiceSessionStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        expires_at=now,
        pipeline_task=None,
        stop_event=asyncio.Event(),
        transcript_buffer=TranscriptBuffer(),
        interruption_state=InterruptionState(),
        trace_id="trace",
    )


async def test_fake_voice_turn_publishes_user_and_assistant_transcripts() -> None:
    event_publisher = InMemoryEventPublisher()
    sink = TranscriptSink(
        sessionmaker=None,
        repository=TranscriptRepository(),
        publisher=TranscriptEventPublisher(event_publisher),
    )
    session = _voice_session()
    await run_fake_voice_turn(
        voice_session=session,
        stt_provider=FakeSpeechToTextProvider(),
        tts_provider=FakeTextToSpeechProvider(),
        transcript_sink=sink,
        event_publisher=event_publisher,
        settings=test_settings(),
    )
    event_types = [event["event_type"] for event in event_publisher.events]
    assert "transcript.final" in event_types
    assert any(
        isinstance(event["payload"], dict) and event["payload"].get("speaker") == "assistant"
        for event in event_publisher.events
    )
