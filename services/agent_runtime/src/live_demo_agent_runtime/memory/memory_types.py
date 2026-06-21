"""Bounded memory update types for the realtime agent brain."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

MEMORY_TYPES: tuple[str, ...] = (
    "persona",
    "pain_point",
    "use_case",
    "objection",
    "buying_signal",
    "feature_interest",
    "question",
    "urgency",
    "preference",
    "unanswered_question",
)


@dataclass(frozen=True, slots=True)
class MemoryUpdate:
    type: str
    content: str
    confidence: float
    importance: float
    evidence_transcript_event_ids: tuple[UUID, ...] = ()
    evidence_screen_ids: tuple[str, ...] = ()
    evidence_action_ids: tuple[str, ...] = ()

    def has_evidence(self) -> bool:
        return bool(
            self.evidence_transcript_event_ids
            or self.evidence_screen_ids
            or self.evidence_action_ids
        )


@dataclass(frozen=True, slots=True)
class StoredMemory:
    memory_id: str
    organization_id: UUID
    demo_session_id: UUID
    update: MemoryUpdate
    content_hash: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class MemoryHandleResult:
    accepted: tuple[StoredMemory, ...]
    rejected: tuple[str, ...]
    merged: tuple[StoredMemory, ...]
