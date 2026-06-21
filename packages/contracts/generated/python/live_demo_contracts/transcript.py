# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: E501, F401, RUF100

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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


class TranscriptEventsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[TranscriptEvent] = Field(default_factory=list)
    next_cursor: str | None


class QuestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    source: str
    transcript_event_id: UuidString | None = None
    insight_id: UuidString | None = None
    created_at: IsoDateTimeString


class QuestionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[QuestionResponse] = Field(default_factory=list)
    next_cursor: str | None
