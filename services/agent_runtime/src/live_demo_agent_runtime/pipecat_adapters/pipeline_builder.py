"""Voice pipeline builder with Pipecat imports isolated.

Verified in this workspace: no Pipecat package is installed, so Phase 7 ships a
fake-provider pipeline that exercises lifecycle, transcript, TTS, and events.
Real Pipecat construction should be added here once the dependency version is pinned.
"""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from live_demo_agent_runtime.agent_brain.host_agent_runner import (
    AgentTurnRequest,
    HostAgentRunner,
)
from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.events import event_types
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.pipeline.placeholder_responder import respond_to_user_transcript
from live_demo_agent_runtime.pipeline.processors.assistant_output_tracker import (
    AssistantOutputTracker,
)
from live_demo_agent_runtime.pipeline.processors.transcript_sink_processor import (
    transcript_chunk_to_write_item,
)
from live_demo_agent_runtime.sessions.voice_session import VoiceSession
from live_demo_agent_runtime.stt.base import SpeechToTextProvider
from live_demo_agent_runtime.stt.transcript_types import AudioFrame, SttOptions
from live_demo_agent_runtime.transcripts.transcript_buffer import TranscriptWriteItem
from live_demo_agent_runtime.transcripts.transcript_sink import TranscriptSink
from live_demo_agent_runtime.transports.base import RealtimeVoiceTransport
from live_demo_agent_runtime.tts.audio_types import TtsRequest
from live_demo_agent_runtime.tts.base import TextToSpeechProvider


@dataclass(slots=True)
class BuiltVoicePipeline:
    task: asyncio.Task[None] | None = None

    async def start(self, runner: AsyncIterator[None]) -> None:
        async def consume() -> None:
            async for _ in runner:
                pass

        self.task = asyncio.create_task(consume())

    async def stop(self) -> None:
        if self.task is not None and not self.task.done():
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)


async def _fake_audio_stream() -> AsyncIterator[AudioFrame]:
    yield AudioFrame(
        audio=b"\x00\x00" * 160,
        sample_rate=16000,
        channels=1,
        sample_width_bytes=2,
        timestamp_ms=0,
        is_final=True,
        metadata={"fake_transcript": "can you show the dashboard?"},
    )


async def run_fake_voice_turn(
    *,
    voice_session: VoiceSession,
    stt_provider: SpeechToTextProvider,
    tts_provider: TextToSpeechProvider,
    transcript_sink: TranscriptSink,
    event_publisher: EventPublisher,
    settings: AgentRuntimeSettings,
    agent_runner: HostAgentRunner | None = None,
) -> None:
    turn_id = uuid4()
    final_user_text = ""
    async for chunk in stt_provider.transcribe_stream(
        _fake_audio_stream(),
        SttOptions(
            language=settings.ai_stt_language,
            enable_partials=settings.ai_stt_enable_partials,
            sample_rate=settings.ai_stt_sample_rate,
            timeout_ms=settings.ai_stt_timeout_ms,
        ),
    ):
        item = transcript_chunk_to_write_item(
            chunk=chunk,
            organization_id=voice_session.organization_id,
            demo_session_id=voice_session.demo_session_id,
            speaker="user",
            turn_id=turn_id,
            persist_partials=settings.transcript_persist_partials,
            persist_finals=settings.transcript_persist_finals,
        )
        await transcript_sink.enqueue(
            voice_session.transcript_buffer,
            item,
            trace_id=voice_session.trace_id,
        )
        if chunk.is_final:
            final_user_text = chunk.text
    if agent_runner is not None and settings.agent_brain_enabled:
        turn_result = await agent_runner.run_turn(
            AgentTurnRequest(
                organization_id=voice_session.organization_id,
                demo_session_id=voice_session.demo_session_id,
                product_id=voice_session.product_id,
                user_utterance=final_user_text,
                user_transcript_event_id=None,
                active_turn_id=turn_id,
                trace_id=voice_session.trace_id,
            )
        )
        response_text = turn_result.decision.spoken_response
    else:
        await event_publisher.publish(
            organization_id=voice_session.organization_id,
            demo_session_id=voice_session.demo_session_id,
            event_type=event_types.AGENT_TURN_STARTED,
            trace_id=voice_session.trace_id,
            payload={"turn_id": str(turn_id)},
        )
        response_text = respond_to_user_transcript(final_user_text)
    assistant_turn_id = uuid4()
    tracker = AssistantOutputTracker(voice_session.interruption_state)
    tracker.start_turn(turn_id=assistant_turn_id, text=response_text, now_ms=0)
    async for audio_chunk in tts_provider.synthesize_stream(
        TtsRequest(
            voice_session_id=voice_session.voice_session_id,
            text=response_text,
            voice=settings.ai_tts_voice,
            sample_rate=settings.ai_tts_sample_rate,
            metadata={"cache_allowed": "false"},
        )
    ):
        tracker.mark_audio_chunk(audio_chunk, now_ms=0)
    assistant_item = TranscriptWriteItem(
        transcript_event_id=uuid4(),
        organization_id=voice_session.organization_id,
        demo_session_id=voice_session.demo_session_id,
        speaker="assistant",
        chunk_type="final",
        text=response_text,
        is_final=True,
        start_ms=None,
        end_ms=None,
        confidence=1.0,
        turn_id=assistant_turn_id,
        created_at=datetime.now(UTC),
        persist=settings.transcript_persist_finals,
        publish=True,
    )
    await transcript_sink.enqueue(
        voice_session.transcript_buffer,
        assistant_item,
        trace_id=voice_session.trace_id,
    )
    tracker.complete()
    if agent_runner is None or not settings.agent_brain_enabled:
        await event_publisher.publish(
            organization_id=voice_session.organization_id,
            demo_session_id=voice_session.demo_session_id,
            event_type=event_types.AGENT_TURN_COMPLETED,
            trace_id=voice_session.trace_id,
            payload={"turn_id": str(turn_id), "assistant_turn_id": str(assistant_turn_id)},
        )


async def build_voice_pipeline(
    voice_session: VoiceSession,
    transport: RealtimeVoiceTransport,
    stt_provider: SpeechToTextProvider,
    tts_provider: TextToSpeechProvider,
    transcript_sink: TranscriptSink,
    settings: AgentRuntimeSettings,
    event_publisher: EventPublisher,
    agent_runner: HostAgentRunner | None = None,
) -> BuiltVoicePipeline:
    del transport

    async def runner() -> AsyncIterator[None]:
        await run_fake_voice_turn(
            voice_session=voice_session,
            stt_provider=stt_provider,
            tts_provider=tts_provider,
            transcript_sink=transcript_sink,
            event_publisher=event_publisher,
            settings=settings,
            agent_runner=agent_runner,
        )
        yield None

    pipeline = BuiltVoicePipeline()
    await pipeline.start(runner())
    return pipeline
