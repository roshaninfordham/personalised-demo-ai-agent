"""FastAPI dependency accessors for runtime singletons."""

from typing import cast

from fastapi import Request

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.sessions.voice_session_manager import VoiceSessionManager
from live_demo_agent_runtime.stt import SttProviderRegistry
from live_demo_agent_runtime.transcripts.transcript_sink import TranscriptSink
from live_demo_agent_runtime.transports.base import RealtimeVoiceTransport
from live_demo_agent_runtime.tts import TtsProviderRegistry


def get_settings_dependency(request: Request) -> AgentRuntimeSettings:
    return cast(AgentRuntimeSettings, request.app.state.settings)


def get_voice_session_manager(request: Request) -> VoiceSessionManager:
    return cast(VoiceSessionManager, request.app.state.voice_session_manager)


def get_stt_registry(request: Request) -> SttProviderRegistry:
    return cast(SttProviderRegistry, request.app.state.stt_registry)


def get_tts_registry(request: Request) -> TtsProviderRegistry:
    return cast(TtsProviderRegistry, request.app.state.tts_registry)


def get_transport(request: Request) -> RealtimeVoiceTransport:
    return cast(RealtimeVoiceTransport, request.app.state.transport_provider)


def get_transcript_sink(request: Request) -> TranscriptSink:
    return cast(TranscriptSink, request.app.state.transcript_sink)


def get_event_publisher(request: Request) -> EventPublisher:
    return cast(EventPublisher, request.app.state.event_publisher)
