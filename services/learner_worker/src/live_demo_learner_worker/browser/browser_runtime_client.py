"""Browser runtime client and fixture client for learner cold-path work."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class BBox:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class UIElement:
    element_id: str
    role: str | None
    label: str | None
    text: str | None = None
    surrounding_text: str | None = None
    bbox: BBox | None = None
    visible: bool = True
    enabled: bool = True
    risk_level: str = "unknown"
    confidence: float = 0.0
    element_fingerprint: str | None = None
    action_type: str | None = None


@dataclass(frozen=True, slots=True)
class SafeAction:
    action_id: str
    action_type: str
    label: str
    risk_level: str = "low"
    score: float = 0.0
    element_id: str | None = None
    element_fingerprint: str | None = None
    requires_confirmation: bool = False
    reason: str | None = None
    target_url: str | None = None
    expires_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ScreenState:
    screen_id: UUID
    product_id: UUID
    organization_id: UUID
    screen_hash: str
    url: str
    url_path: str | None
    title: str | None
    visible_text: str | None
    summary: str | None = None
    confidence: float = 0.0
    screenshot_artifact_id: UUID | None = None
    dom_summary: Mapping[str, object] | None = None
    accessibility_summary: Mapping[str, object] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class BrowserScreenRead:
    screen_state: ScreenState
    ui_elements: tuple[UIElement, ...]
    safe_actions: tuple[SafeAction, ...]


@dataclass(frozen=True, slots=True)
class BrowserActionResult:
    action_id: str
    success: bool
    latency_ms: int
    resulting_screen: BrowserScreenRead | None = None
    error_code: str | None = None
    error_message: str | None = None


class BrowserRuntimeClient(Protocol):
    async def read_current_screen(self, product_id: UUID) -> BrowserScreenRead: ...

    async def execute_action(self, action: SafeAction) -> BrowserActionResult: ...

    async def go_back(self) -> BrowserActionResult: ...

    async def navigate_to(self, url: str) -> BrowserScreenRead: ...


class FakeBrowserRuntimeClient:
    """Deterministic browser runtime for CI and local unit tests."""

    def __init__(self, screens: Sequence[BrowserScreenRead] | None = None) -> None:
        self._screens = list(screens or [])
        self._index = 0
        self.executed_actions: list[str] = []

    def add_screen(self, screen: BrowserScreenRead) -> None:
        self._screens.append(screen)

    async def read_current_screen(self, product_id: UUID) -> BrowserScreenRead:
        if not self._screens:
            self._screens.append(make_fixture_screen(product_id=product_id))
        return self._screens[self._index]

    async def execute_action(self, action: SafeAction) -> BrowserActionResult:
        self.executed_actions.append(action.action_id)
        if self._screens and self._index < len(self._screens) - 1:
            self._index += 1
        resulting = self._screens[self._index] if self._screens else None
        return BrowserActionResult(
            action_id=action.action_id,
            success=action.risk_level in {"low", "medium"},
            latency_ms=25,
            resulting_screen=resulting,
            error_code=None if action.risk_level in {"low", "medium"} else "risk_blocked",
        )

    async def go_back(self) -> BrowserActionResult:
        if self._index > 0:
            self._index -= 1
        return BrowserActionResult(
            action_id="go_back",
            success=True,
            latency_ms=10,
            resulting_screen=self._screens[self._index] if self._screens else None,
        )

    async def navigate_to(self, url: str) -> BrowserScreenRead:
        _ = url
        if not self._screens:
            self._screens.append(make_fixture_screen())
        self._index = 0
        return self._screens[0]


def make_fixture_screen(
    *,
    organization_id: UUID | None = None,
    product_id: UUID | None = None,
    screen_hash: str = "screen-dashboard",
    title: str = "Dashboard",
    visible_text: str = "Dashboard Revenue Metrics Reports Add Metric",
    risk_level: str = "low",
) -> BrowserScreenRead:
    organization = organization_id or uuid4()
    product = product_id or uuid4()
    screen = ScreenState(
        screen_id=uuid4(),
        organization_id=organization,
        product_id=product,
        screen_hash=screen_hash,
        url="https://example.com/dashboard",
        url_path="/dashboard",
        title=title,
        visible_text=visible_text,
        summary=None,
        confidence=0.8,
        dom_summary={"headings": [title], "buttons": 2, "links": 2, "inputs": 0},
        accessibility_summary={"landmarks": ["navigation", "main"]},
    )
    elements = (
        UIElement(
            element_id="el_add_metric",
            role="button",
            label="Add Metric",
            text="Add Metric",
            bbox=BBox(100, 100, 120, 32),
            visible=True,
            enabled=True,
            risk_level=risk_level,
            confidence=0.9,
            element_fingerprint="button:add-metric",
            action_type="click_element",
        ),
        UIElement(
            element_id="el_reports",
            role="link",
            label="Reports",
            text="Reports",
            bbox=BBox(20, 160, 80, 24),
            visible=True,
            enabled=True,
            risk_level="low",
            confidence=0.9,
            element_fingerprint="link:reports",
            action_type="click_element",
        ),
    )
    actions = (
        SafeAction(
            action_id="act_add_metric",
            action_type="click_element",
            label="Add Metric",
            risk_level=risk_level,
            score=0.9,
            element_id="el_add_metric",
            element_fingerprint="button:add-metric",
            reason="Visible button.",
        ),
        SafeAction(
            action_id="act_reports",
            action_type="click_element",
            label="Reports",
            risk_level="low",
            score=0.8,
            element_id="el_reports",
            element_fingerprint="link:reports",
            reason="Visible navigation link.",
        ),
    )
    return BrowserScreenRead(screen_state=screen, ui_elements=elements, safe_actions=actions)
