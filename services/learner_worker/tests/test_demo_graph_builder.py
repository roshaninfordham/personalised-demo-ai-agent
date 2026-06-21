from __future__ import annotations

from uuid import uuid4

from live_demo_learner_worker.browser.browser_runtime_client import (
    BrowserActionResult,
    make_fixture_screen,
)
from live_demo_learner_worker.demo_graph.graph_algorithms import find_shortest_safe_path
from live_demo_learner_worker.demo_graph.graph_builder import DemoGraphBuilder
from live_demo_learner_worker.demo_graph.graph_confidence import (
    incremental_average,
    laplace_confidence,
)


def test_creates_screen_node_and_action_edge() -> None:
    screen = make_fixture_screen()
    builder = DemoGraphBuilder()
    edge = builder.add_observed_edge(
        from_read=screen,
        action=screen.safe_actions[0],
        result=BrowserActionResult(
            action_id=screen.safe_actions[0].action_id,
            success=True,
            latency_ms=42,
            resulting_screen=make_fixture_screen(
                product_id=screen.screen_state.product_id, screen_hash="reports"
            ),
        ),
    )

    assert edge.success_count == 1
    assert len(builder.graph.nodes_by_hash) == 2


def test_confidence_and_path_algorithms() -> None:
    assert laplace_confidence(1, 0) == 0.667
    assert incremental_average(100, 1, 200) == 150
    screen = make_fixture_screen()
    builder = DemoGraphBuilder()
    target = make_fixture_screen(product_id=screen.screen_state.product_id, screen_hash="target")
    edge = builder.add_observed_edge(
        from_read=screen,
        action=screen.safe_actions[0],
        result=BrowserActionResult("a", True, 1, target),
    )
    path = find_shortest_safe_path(
        builder.graph.edges, edge.from_screen_id, edge.to_screen_id or uuid4()
    )
    assert path == [edge]
