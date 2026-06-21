"""Internal voice session lifecycle API."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.dependencies import (
    get_event_publisher,
    get_settings_dependency,
    get_stt_registry,
    get_transcript_sink,
    get_transport,
    get_tts_registry,
    get_voice_session_manager,
)
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.pipecat_adapters.pipeline_builder import build_voice_pipeline
from live_demo_agent_runtime.pipeline.processors.session_state_processor import (
    voice_session_payload,
)
from live_demo_agent_runtime.sessions.voice_session_manager import VoiceSessionManager
from live_demo_agent_runtime.stt import SttProviderRegistry
from live_demo_agent_runtime.transcripts.transcript_sink import TranscriptSink
from live_demo_agent_runtime.transports.base import RealtimeVoiceTransport
from live_demo_agent_runtime.tts import TtsProviderRegistry

router = APIRouter(prefix="/internal/agent/v1/voice-sessions", tags=["voice-sessions"])
ManagerDep = Annotated[VoiceSessionManager, Depends(get_voice_session_manager)]
SttRegistryDep = Annotated[SttProviderRegistry, Depends(get_stt_registry)]
TtsRegistryDep = Annotated[TtsProviderRegistry, Depends(get_tts_registry)]
TransportDep = Annotated[RealtimeVoiceTransport, Depends(get_transport)]
TranscriptSinkDep = Annotated[TranscriptSink, Depends(get_transcript_sink)]
SettingsDep = Annotated[AgentRuntimeSettings, Depends(get_settings_dependency)]
EventPublisherDep = Annotated[EventPublisher, Depends(get_event_publisher)]


class CreateVoiceSessionRequest(BaseModel):
    organization_id: UUID
    demo_session_id: UUID
    product_id: UUID
    transport_provider: str = "small_webrtc"
    trace_id: str = Field(default="trace-local", min_length=1, max_length=128)


class VoiceSessionResponse(BaseModel):
    voice_session_id: UUID
    status: str
    transport_provider: str
    join_config: dict[str, object] | None = None


@router.post("")
async def create_voice_session(
    request: CreateVoiceSessionRequest,
    manager: ManagerDep,
) -> dict[str, object]:
    session, join_config = await manager.create_session(
        organization_id=request.organization_id,
        demo_session_id=request.demo_session_id,
        product_id=request.product_id,
        transport_provider=request.transport_provider,
        trace_id=request.trace_id,
    )
    return {
        "voice_session_id": str(session.voice_session_id),
        "status": session.status.value,
        "transport_provider": session.transport_provider,
        "join_config": join_config.to_response(),
    }


@router.get("/{voice_session_id}")
async def get_voice_session(
    voice_session_id: UUID,
    manager: ManagerDep,
) -> dict[str, object]:
    return voice_session_payload(manager.get(voice_session_id))


@router.post("/{voice_session_id}/start")
async def start_voice_session(
    voice_session_id: UUID,
    manager: ManagerDep,
    stt_registry: SttRegistryDep,
    tts_registry: TtsRegistryDep,
    transport: TransportDep,
    transcript_sink: TranscriptSinkDep,
    settings: SettingsDep,
    event_publisher: EventPublisherDep,
) -> dict[str, object]:
    session = await manager.start_session(voice_session_id)
    if session.pipeline_task is None or session.pipeline_task.done():
        pipeline = await build_voice_pipeline(
            voice_session=session,
            transport=transport,
            stt_provider=stt_registry.get_provider(),
            tts_provider=tts_registry.get_provider(),
            transcript_sink=transcript_sink,
            settings=settings,
            event_publisher=event_publisher,
        )
        session.pipeline_task = pipeline.task
    return voice_session_payload(session)


@router.post("/{voice_session_id}/stop")
async def stop_voice_session(
    voice_session_id: UUID,
    manager: ManagerDep,
) -> dict[str, object]:
    return voice_session_payload(await manager.stop_session(voice_session_id))


@router.get("/{voice_session_id}/join-config")
async def get_voice_session_join_config(
    voice_session_id: UUID,
    manager: ManagerDep,
) -> dict[str, object]:
    _session = manager.get(voice_session_id)
    return (await manager.get_join_config(voice_session_id)).to_response()
