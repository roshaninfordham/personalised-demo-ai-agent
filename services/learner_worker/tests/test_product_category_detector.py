from __future__ import annotations

from live_demo_learner_worker.browser.browser_runtime_client import make_fixture_screen
from live_demo_learner_worker.classification.product_category_detector import (
    ProductCategoryDetector,
)


def test_analytics_dashboard_category_detected() -> None:
    screen = make_fixture_screen()
    result = ProductCategoryDetector().detect(
        screen_summary="Dashboard with revenue metrics and reports.",
        visible_text=screen.screen_state.visible_text,
        elements=screen.ui_elements,
        product_name="Metric Master",
        guidance_text="Show KPI reporting.",
        safe_actions=screen.safe_actions,
    )

    assert result.category == "analytics_dashboard"
    assert "founder" in result.target_personas


def test_unknown_category_when_evidence_weak() -> None:
    result = ProductCategoryDetector().detect(
        screen_summary="Welcome.",
        visible_text="Welcome",
        elements=(),
        product_name=None,
        guidance_text=None,
        safe_actions=(),
    )

    assert result.category == "unknown"
