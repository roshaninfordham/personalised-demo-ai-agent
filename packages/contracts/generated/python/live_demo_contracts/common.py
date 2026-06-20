# Generated from packages/contracts/schemas. Do not edit manually.

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

type UuidString = str


type IsoDateTimeString = str


type TraceId = str


type ProviderName = str


type JsonValue = str | float | int | bool | None


type Metadata = dict[str, JsonValue]


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class PolicyDecision(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    CONFIRMATION_REQUIRED = "confirmation_required"


class DemoPhase(StrEnum):
    CREATED = "created"
    PREWARMING = "prewarming"
    DISCOVERY = "discovery"
    OVERVIEW = "overview"
    CORE_WORKFLOW = "core_workflow"
    DEEP_DIVE = "deep_dive"
    Q_AND_A = "q_and_a"
    SUMMARY = "summary"
    RECOVERY = "recovery"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(StrEnum):
    CREATED = "created"
    PREWARMING = "prewarming"
    WAITING_FOR_USER = "waiting_for_user"
    LIVE = "live"
    ENDING = "ending"
    COMPLETED = "completed"
    FAILED = "failed"


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    width: float
    height: float
