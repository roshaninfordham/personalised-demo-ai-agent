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


class ElementRole(StrEnum):
    BUTTON = "button"
    LINK = "link"
    INPUT = "input"
    TEXTAREA = "textarea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    NAVIGATION = "navigation"
    TAB = "tab"
    TABLE = "table"
    CHART = "chart"
    CARD = "card"
    MODAL = "modal"
    TEXT = "text"
    UNKNOWN = "unknown"


class UIElement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    element_id: str
    role: ElementRole
    label: str
    bbox: BoundingBox
    visible: bool
    enabled: bool
    risk_level: RiskLevel
    confidence: float


class ScreenSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    screen_id: UuidString
    summary: str
    confidence: float
    created_at: IsoDateTimeString


class ScreenState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    screen_id: UuidString
    session_id: UuidString
    browser_session_id: str
    url: str
    title: str
    screen_hash: str
    visible_text: list[str] = Field(default_factory=list)
    summary: ScreenSummary
    elements: list[UIElement] = Field(default_factory=list)
    screenshot_uri: str
    confidence: float
    created_at: IsoDateTimeString
