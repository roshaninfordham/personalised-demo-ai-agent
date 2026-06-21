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


class BrowserActionType(StrEnum):
    READ_CURRENT_SCREEN = "read_current_screen"
    HIGHLIGHT_ELEMENT = "highlight_element"
    CLICK_ELEMENT = "click_element"
    TYPE_INTO_ELEMENT = "type_into_element"
    TYPE_DEMO_TEXT = "type_demo_text"
    SCROLL = "scroll"
    GO_BACK = "go_back"
    NAVIGATE_TO_ALLOWED_URL = "navigate_to_allowed_url"
    WAIT_FOR_IDLE = "wait_for_idle"
    TAKE_SCREENSHOT = "take_screenshot"


class ScrollDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class BrowserActionCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: UuidString
    session_id: UuidString
    browser_session_id: str
    action_type: BrowserActionType
    created_at: IsoDateTimeString
    element_id: str | None = None
    text: str | None = None
    direction: ScrollDirection | None = None
    url: str | None = None
    requires_cursor_animation: bool = True
    policy_context: Metadata | None = None


class BrowserActionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    browser_action_id: UuidString | None = None
    command_id: UuidString
    session_id: UuidString
    success: bool
    policy_decision: PolicyDecision
    risk_level: RiskLevel
    latency_ms: int
    created_at: IsoDateTimeString
    from_screen_id: UuidString | None = None
    to_screen_id: UuidString | None = None
    new_screen_summary: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class BrowserActionEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_event_id: UuidString
    action_type: str
    risk_level: RiskLevel
    policy_decision: PolicyDecision
    success: bool | None = None
    error_code: str | None = None
    from_screen_id: UuidString | None = None
    to_screen_id: UuidString | None = None
    latency_ms: int | None = None
    created_at: IsoDateTimeString
    action_payload: Metadata | None = None


class BrowserActionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[BrowserActionEventResponse] = Field(default_factory=list)
    next_cursor: str | None


class SafeAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: UuidString
    action_type: BrowserActionType
    label: str
    element_id: str | None = None
    risk_level: RiskLevel
    policy_decision: PolicyDecision
    confidence: float
    reason: str | None = None


class CursorMoveEventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    duration_ms: int


class ElementHighlightEventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    element_id: str
    duration_ms: int | None = None
