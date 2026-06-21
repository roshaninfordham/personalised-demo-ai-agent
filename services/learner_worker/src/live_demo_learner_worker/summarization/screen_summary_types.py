"""Types for first-screen summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from live_demo_learner_worker.browser.browser_runtime_client import (
    SafeAction,
    ScreenState,
    UIElement,
)


@dataclass(frozen=True, slots=True)
class FirstScreenSummaryInput:
    organization_id: UUID
    product_id: UUID
    session_id: UUID | None
    screen_state: ScreenState
    ui_elements: tuple[UIElement, ...]
    visible_text: str | None
    safe_actions: tuple[SafeAction, ...]
    screenshot_artifact_id: UUID | None
    trace_id: str


@dataclass(frozen=True, slots=True)
class ScreenSummary:
    screen_id: UUID
    summary: str
    screen_type: str
    visible_capabilities: tuple[str, ...]
    safe_action_labels: tuple[str, ...]
    unknowns: tuple[str, ...]
    confidence: float
    sources: tuple[str, ...]
    metadata: dict[str, object] = field(default_factory=dict)
