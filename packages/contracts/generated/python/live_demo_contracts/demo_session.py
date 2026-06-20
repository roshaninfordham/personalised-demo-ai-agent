# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: F401

from __future__ import annotations

from enum import StrEnum

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


class DemoSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UuidString
    product_id: UuidString
    product_url: str
    status: SessionStatus
    current_phase: DemoPhase
    created_at: IsoDateTimeString
    updated_at: IsoDateTimeString
    product_name: str | None = None
    target_persona: str | None = None
    recipe_id: UuidString | None = None
    browser_session_id: str | None = None
    transport_session_id: str | None = None
    started_at: IsoDateTimeString | None = None
    ended_at: IsoDateTimeString | None = None


class CreateDemoSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_url: str
    product_name: str | None = None
    target_persona: str | None = None
    positioning: str | None = None
    demo_goals: list[str] = Field(default_factory=list)
    what_to_show: list[str] = Field(default_factory=list)
    what_to_avoid: list[str] = Field(default_factory=list)
    recipe_id: UuidString | None = None
    metadata: Metadata | None = None


class CreateDemoSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: DemoSession


class StartDemoSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UuidString


class StartDemoSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: DemoSession


class EndDemoSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: UuidString
    reason: str | None = None


class EndDemoSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: DemoSession
