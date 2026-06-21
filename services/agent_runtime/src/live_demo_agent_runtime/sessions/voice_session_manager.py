"""Voice session manager with deterministic lifecycle transitions."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.errors import VoiceSessionLimitError, VoiceSessionNotFoundError
from live_demo_agent_runtime.events import event_types
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.sessions.session_locks import SessionLockRegistry
from live_demo_agent_runtime.sessions.session_state import VoiceSessionStatus
from live_demo_agent_runtime.sessions.voice_session import VoiceSession
from live_demo_agent_runtime.transcripts.transcript_buffer import TranscriptBuffer
from live_demo_agent_runtime.transcripts.transcript_sink import TranscriptSink
from live_demo_agent_runtime.transports.base import RealtimeVoiceTransport
from live_demo_agent_runtime.transports.join_config import VoiceJoinConfig
from live_demo_agent_runtime.vad.interruption_state import InterruptionState


class VoiceSessionManager:
    def __init__(
        self,
        *,
        settings: AgentRuntimeSettings,
        event_publisher: EventPublisher,
        transport: RealtimeVoiceTransport,
        transcript_sink: TranscriptSink | None = None,
    ) -> None:
        self._settings = settings
        self._event_publisher = event_publisher
        self._transport = transport
        self._transcript_sink = transcript_sink
        self._sessions: dict[UUID, VoiceSession] = {}
        self._by_demo_session: dict[UUID, UUID] = {}
        self._locks = SessionLockRegistry()
        self._shutdown = False

    @property
    def active_count(self) -> int:
        return sum(1 for session in self._sessions.values() if not session.is_terminal)

    def get(self, voice_session_id: UUID) -> VoiceSession:
        session = self._sessions.get(voice_session_id)
        if session is None:
            raise VoiceSessionNotFoundError()
        return session

    async def get_join_config(self, voice_session_id: UUID) -> VoiceJoinConfig:
        self.get(voice_session_id)
        return await self._transport.get_join_config(voice_session_id)

    async def create_session(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        product_id: UUID,
        transport_provider: str,
        trace_id: str,
    ) -> tuple[VoiceSession, VoiceJoinConfig]:
        existing_id = self._by_demo_session.get(demo_session_id)
        if existing_id is not None:
            existing = self._sessions[existing_id]
            if not existing.is_terminal:
                return existing, await self._transport.get_join_config(existing.voice_session_id)
        if self.active_count >= self._settings.voice_session_max_active:
            raise VoiceSessionLimitError()
        now = datetime.now(UTC)
        voice_session_id = uuid4()
        session = VoiceSession(
            voice_session_id=voice_session_id,
            organization_id=organization_id,
            demo_session_id=demo_session_id,
            product_id=product_id,
            transport_provider=transport_provider,
            status=VoiceSessionStatus.CREATED,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(seconds=self._settings.voice_session_ttl_seconds),
            pipeline_task=None,
            stop_event=asyncio.Event(),
            transcript_buffer=TranscriptBuffer(self._settings.transcript_buffer_max_items),
            interruption_state=InterruptionState(),
            trace_id=trace_id,
        )
        session.transition_to(VoiceSessionStatus.STARTING)
        await self._transport.create_session(
            voice_session_id=voice_session_id,
            organization_id=organization_id,
            demo_session_id=demo_session_id,
            product_id=product_id,
            expires_at=session.expires_at,
        )
        session.transition_to(VoiceSessionStatus.WAITING_FOR_CLIENT)
        self._sessions[voice_session_id] = session
        self._by_demo_session[demo_session_id] = voice_session_id
        join_config = await self._transport.get_join_config(voice_session_id)
        await self._event_publisher.publish(
            organization_id=organization_id,
            demo_session_id=demo_session_id,
            event_type=event_types.VOICE_SESSION_CREATED,
            trace_id=trace_id,
            payload={"voice_session_id": str(voice_session_id), "status": session.status.value},
        )
        return session, join_config

    async def start_session(self, voice_session_id: UUID) -> VoiceSession:
        session = self.get(voice_session_id)
        async with self._locks.lock_for(voice_session_id):
            if session.status == VoiceSessionStatus.WAITING_FOR_CLIENT:
                session.transition_to(VoiceSessionStatus.CONNECTED)
            if session.status == VoiceSessionStatus.CONNECTED:
                session.transition_to(VoiceSessionStatus.ACTIVE)
            await self._event_publisher.publish(
                organization_id=session.organization_id,
                demo_session_id=session.demo_session_id,
                event_type=event_types.VOICE_SESSION_ACTIVE,
                trace_id=session.trace_id,
                payload={"voice_session_id": str(voice_session_id), "status": session.status.value},
            )
            return session

    async def stop_session(self, voice_session_id: UUID) -> VoiceSession:
        session = self.get(voice_session_id)
        async with self._locks.lock_for(voice_session_id):
            if session.is_terminal:
                return session
            if not session.is_terminal and session.status != VoiceSessionStatus.STOPPING:
                session.transition_to(VoiceSessionStatus.STOPPING)
            session.stop_event.set()
            if session.pipeline_task is not None and not session.pipeline_task.done():
                session.pipeline_task.cancel()
                await asyncio.gather(session.pipeline_task, return_exceptions=True)
            await self._transport.close(voice_session_id)
            flush_failed = False
            if self._transcript_sink is not None:
                try:
                    await self._transcript_sink.flush(session.transcript_buffer)
                except Exception:
                    flush_failed = True
            if session.status == VoiceSessionStatus.STOPPING:
                session.transition_to(
                    VoiceSessionStatus.FAILED if flush_failed else VoiceSessionStatus.STOPPED
                )
            await self._event_publisher.publish(
                organization_id=session.organization_id,
                demo_session_id=session.demo_session_id,
                event_type=(
                    event_types.VOICE_SESSION_FAILED
                    if flush_failed
                    else event_types.VOICE_SESSION_STOPPED
                ),
                trace_id=session.trace_id,
                payload={"voice_session_id": str(voice_session_id), "status": session.status.value},
            )
            self._locks.discard(voice_session_id)
            return session

    async def cleanup_expired_sessions(self) -> int:
        now = datetime.now(UTC)
        expired = [
            session.voice_session_id
            for session in self._sessions.values()
            if not session.is_terminal and session.expires_at <= now
        ]
        for voice_session_id in expired:
            session = self.get(voice_session_id)
            if session.status == VoiceSessionStatus.WAITING_FOR_CLIENT:
                session.transition_to(VoiceSessionStatus.EXPIRED)
            else:
                await self.stop_session(voice_session_id)
        return len(expired)

    async def shutdown(self) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        active_ids = [
            session.voice_session_id
            for session in self._sessions.values()
            if not session.is_terminal
        ]
        await asyncio.gather(
            *(self.stop_session(voice_session_id) for voice_session_id in active_ids)
        )
