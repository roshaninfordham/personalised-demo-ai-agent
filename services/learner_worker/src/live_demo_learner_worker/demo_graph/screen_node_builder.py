"""Screen node construction."""

from __future__ import annotations

from live_demo_learner_worker.browser.browser_runtime_client import BrowserScreenRead
from live_demo_learner_worker.demo_graph.graph_types import DemoGraphScreenNode


def build_screen_node(
    screen_read: BrowserScreenRead, *, screen_type: str | None = None
) -> DemoGraphScreenNode:
    screen = screen_read.screen_state
    features = tuple(
        sorted(
            {
                (element.role or "unknown")
                for element in screen_read.ui_elements
                if element.visible and element.enabled
            }
        )
    )
    risk_level = "low"
    if any(action.risk_level in {"high", "blocked"} for action in screen_read.safe_actions):
        risk_level = "medium"
    return DemoGraphScreenNode(
        screen_id=screen.screen_id,
        product_id=screen.product_id,
        screen_hash=screen.screen_hash,
        url_path=screen.url_path,
        title=screen.title,
        summary=screen.summary,
        screen_type=screen_type,
        features=features,
        risk_level=risk_level,
        confidence=screen.confidence,
    )
