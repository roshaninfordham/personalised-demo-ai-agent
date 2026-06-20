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
    start_url: str
    status: SessionStatus
    current_phase: DemoPhase
    created_at: IsoDateTimeString
    updated_at: IsoDateTimeString
    product_name: str | None = None
    user_persona: str | None = None
    user_company: str | None = None
    user_display_name: str | None = None
    user_email: str | None = None
    recipe_id: UuidString | None = None
    browser_session_id: str | None = None
    transport_session_id: str | None = None
    started_at: IsoDateTimeString | None = None
    ended_at: IsoDateTimeString | None = None


class CreateDemoSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UuidString
    recipe_id: UuidString | None = None
    start_url: str | None = None
    user_persona: str | None = None
    user_company: str | None = None
    user_display_name: str | None = None
    user_email: str | None = None


class CreateDemoSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: DemoSession


class StartDemoSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pass


class StartDemoSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: DemoSession
    join_config: JoinConfigResponse


class EndDemoSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = None
    force: bool | None = None


class EndDemoSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: DemoSession


type DemoSessionResponse = DemoSession


class ListDemoSessionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[DemoSession] = Field(default_factory=list)
    next_cursor: str | None


class SessionLiveState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    available: bool
    current_screen: Metadata | None
    safe_actions: list[Metadata] = Field(default_factory=list)
    browser_status: Metadata | None
    latency: Metadata
    live_state_status: str | None = None


class DemoSessionStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: DemoSession
    live_state: SessionLiveState


class JoinConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transport_provider: str
    session_id: UuidString
    room_id: str
    join_token: str | None
    expires_at: IsoDateTimeString
    status: str
