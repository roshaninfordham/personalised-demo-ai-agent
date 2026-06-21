from __future__ import annotations

from live_demo_learner_worker.browser.browser_runtime_client import (
    BrowserActionResult,
    make_fixture_screen,
)
from live_demo_learner_worker.demo_graph.graph_builder import DemoGraphBuilder
from live_demo_learner_worker.routes.generated_route_builder import GeneratedRouteBuilder


def test_generated_route_contains_required_steps() -> None:
    screen = make_fixture_screen()
    builder = DemoGraphBuilder()
    builder.upsert_screen(screen, screen_type="dashboard_or_overview")
    builder.add_observed_edge(
        from_read=screen,
        action=screen.safe_actions[0],
        result=BrowserActionResult(
            "a",
            True,
            25,
            make_fixture_screen(product_id=screen.screen_state.product_id, screen_hash="reports"),
        ),
    )

    route = GeneratedRouteBuilder().build(
        product_id=screen.screen_state.product_id,
        nodes=list(builder.graph.nodes_by_hash.values()),
        edges=builder.graph.edges,
    )

    assert [step.step_key for step in route.steps][:2] == ["overview", "core_workflow"]
    assert route.status == "draft"
