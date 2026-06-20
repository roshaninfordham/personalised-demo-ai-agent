# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: F401

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from live_demo_contracts.common import (
    BoundingBox,
    DemoPhase,
    IsoDateTimeString,
    JsonValue,
    Metadata,
    PolicyDecision,
    ProviderName,
    RiskLevel,
    SessionStatus,
    TraceId,
    UuidString,
)


class TranscriptSpeaker(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class TranscriptChunkType(StrEnum):
    PARTIAL = "partial"
    FINAL = "final"
    INTERRUPTED = "interrupted"


class TranscriptEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript_event_id: UuidString
    session_id: UuidString
    speaker: TranscriptSpeaker
    chunk_type: TranscriptChunkType
    text: str
    created_at: IsoDateTimeString
    start_ms: int | None = None
    end_ms: int | None = None
    confidence: float | None = None
    turn_id: str | None = None
