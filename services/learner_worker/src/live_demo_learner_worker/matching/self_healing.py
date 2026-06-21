"""Self-healing for changed UI element references."""

from __future__ import annotations

from dataclasses import dataclass

from live_demo_learner_worker.browser.browser_runtime_client import BrowserScreenRead, UIElement
from live_demo_learner_worker.matching.element_matcher import ElementMatcher
from live_demo_learner_worker.matching.screen_matcher import ScreenMatcher


@dataclass(frozen=True, slots=True)
class SelfHealingResult:
    healed: bool
    new_element_id: str | None
    similarity: float
    confidence: float
    reason: str


class SelfHealingMatcher:
    def __init__(self, screen_matcher: ScreenMatcher, element_matcher: ElementMatcher) -> None:
        self._screen_matcher = screen_matcher
        self._element_matcher = element_matcher

    def heal(
        self,
        *,
        expected_screen: BrowserScreenRead,
        current_screen: BrowserScreenRead,
        expected_element: UIElement,
    ) -> SelfHealingResult:
        screen_match = self._screen_matcher.match(expected_screen, current_screen)
        if screen_match.decision == "not_match":
            return SelfHealingResult(
                False, None, screen_match.similarity_score, 0.0, "screen_mismatch"
            )
        element_match = self._element_matcher.best_match(
            expected_element, current_screen.ui_elements
        )
        if element_match.element is None:
            return SelfHealingResult(
                False, None, element_match.similarity_score, 0.0, "element_not_found"
            )
        return SelfHealingResult(
            True,
            element_match.element.element_id,
            element_match.similarity_score,
            element_match.similarity_score,
            "Matched role, label, action type, and surrounding deterministic features.",
        )
