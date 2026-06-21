"""In-memory graph builder for learner observations."""

from __future__ import annotations

from dataclasses import dataclass, field

from live_demo_learner_worker.browser.browser_runtime_client import (
    BrowserActionResult,
    BrowserScreenRead,
    SafeAction,
)
from live_demo_learner_worker.demo_graph.action_edge_builder import build_action_edge
from live_demo_learner_worker.demo_graph.graph_types import DemoGraphActionEdge, DemoGraphScreenNode
from live_demo_learner_worker.demo_graph.screen_node_builder import build_screen_node


@dataclass(slots=True)
class DemoGraph:
    nodes_by_hash: dict[str, DemoGraphScreenNode] = field(default_factory=dict)
    edges: list[DemoGraphActionEdge] = field(default_factory=list)


class DemoGraphBuilder:
    def __init__(self) -> None:
        self.graph = DemoGraph()

    def upsert_screen(
        self, screen_read: BrowserScreenRead, *, screen_type: str | None = None
    ) -> DemoGraphScreenNode:
        existing = self.graph.nodes_by_hash.get(screen_read.screen_state.screen_hash)
        if existing is not None:
            return existing
        node = build_screen_node(screen_read, screen_type=screen_type)
        self.graph.nodes_by_hash[node.screen_hash] = node
        return node

    def add_observed_edge(
        self,
        *,
        from_read: BrowserScreenRead,
        action: SafeAction,
        result: BrowserActionResult,
    ) -> DemoGraphActionEdge:
        from_node = self.upsert_screen(from_read)
        to_node = self.upsert_screen(result.resulting_screen) if result.resulting_screen else None
        edge = build_action_edge(
            from_node=from_node,
            to_node=to_node,
            action=action,
            latency_ms=result.latency_ms,
            success=result.success,
        )
        self.graph.edges.append(edge)
        return edge
