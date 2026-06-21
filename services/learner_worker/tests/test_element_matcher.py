from __future__ import annotations

from dataclasses import replace

from live_demo_learner_worker.browser.browser_runtime_client import make_fixture_screen
from live_demo_learner_worker.matching.element_matcher import ElementMatcher


def test_same_label_role_matches() -> None:
    element = make_fixture_screen().ui_elements[0]

    result = ElementMatcher().best_match(element, (element,))

    assert result.decision == "matched"


def test_high_risk_element_not_selected() -> None:
    element = make_fixture_screen().ui_elements[0]
    risky = replace(element, element_id="danger", risk_level="blocked")

    result = ElementMatcher().best_match(element, (risky,))

    assert result.element is None
