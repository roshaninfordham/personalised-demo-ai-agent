"""Action edge construction."""

from __future__ import annotations

from uuid import uuid4

from live_demo_learner_worker.browser.browser_runtime_client import SafeAction
from live_demo_learner_worker.demo_graph.graph_confidence import laplace_confidence
from live_demo_learner_worker.demo_graph.graph_types import DemoGraphActionEdge, DemoGraphScreenNode


def build_action_edge(
    *,
    from_node: DemoGraphScreenNode,
    to_node: DemoGraphScreenNode | None,
    action: SafeAction,
    latency_ms: int | None,
    success: bool,
) -> DemoGraphActionEdge:
    success_count = 1 if success else 0
    failure_count = 0 if success else 1
    return DemoGraphActionEdge(
        edge_id=uuid4(),
        product_id=from_node.product_id,
        from_screen_id=from_node.screen_id,
        to_screen_id=to_node.screen_id if to_node is not None else None,
        action_type=action.action_type,
        action_label=action.label,
        element_fingerprint=action.element_fingerprint,
        risk_level=action.risk_level,
        success_count=success_count,
        failure_count=failure_count,
        average_latency_ms=latency_ms,
        confidence=laplace_confidence(success_count, failure_count),
    )
