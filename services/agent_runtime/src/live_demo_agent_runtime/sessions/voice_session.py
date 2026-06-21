"""Voice session runtime record."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from live_demo_agent_runtime.sessions.session_state import (
    VoiceSessionStatus,
    validate_transition,
)
from live_demo_agent_runtime.transcripts.transcript_buffer import TranscriptBuffer
from live_demo_agent_runtime.vad.interruption_state import InterruptionState


@dataclass(slots=True)
class VoiceSession:
    voice_session_id: UUID
    organization_id: UUID
    demo_session_id: UUID
    product_id: UUID
    transport_provider: str
    status: VoiceSessionStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    pipeline_task: asyncio.Task[None] | None
    stop_event: asyncio.Event
    transcript_buffer: TranscriptBuffer
    interruption_state: InterruptionState
    trace_id: str

    def transition_to(self, next_status: VoiceSessionStatus) -> None:
        validate_transition(self.status, next_status)
        self.status = next_status
        self.updated_at = datetime.now(UTC)

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            VoiceSessionStatus.STOPPED,
            VoiceSessionStatus.FAILED,
            VoiceSessionStatus.EXPIRED,
        }
