"""Generated route builder for zero-guidance demos."""

from __future__ import annotations

from uuid import UUID, uuid4

from live_demo_learner_worker.demo_graph.graph_algorithms import (
    get_best_edges_from_screen,
    rank_screens_by_demo_value,
)
from live_demo_learner_worker.demo_graph.graph_types import DemoGraphActionEdge, DemoGraphScreenNode
from live_demo_learner_worker.routes.route_scoring import (
    action_demo_value,
    route_confidence,
    screen_demo_value,
)
from live_demo_learner_worker.routes.route_types import (
    GeneratedDemoRoute,
    GeneratedRouteStep,
    make_step,
)


class GeneratedRouteBuilder:
    def __init__(self, *, max_steps: int = 5) -> None:
        self._max_steps = max_steps

    def build(
        self,
        *,
        product_id: UUID,
        nodes: list[DemoGraphScreenNode],
        edges: list[DemoGraphActionEdge],
    ) -> GeneratedDemoRoute:
        ranked_nodes = rank_screens_by_demo_value(nodes)
        overview = ranked_nodes[0] if ranked_nodes else None
        steps: list[GeneratedRouteStep] = []
        if overview is not None:
            steps.append(
                make_step(
                    step_order=0,
                    step_key="overview",
                    phase="overview",
                    goal="Explain the current visible product screen.",
                    screen_id=overview.screen_id,
                    recommended_action_id=None,
                    recommended_action_label=None,
                    confidence=screen_demo_value(overview),
                    evidence={"screen_hash": overview.screen_hash},
                )
            )
            best_edges = sorted(
                get_best_edges_from_screen(edges, overview.screen_id, limit=5),
                key=lambda edge: (
                    -action_demo_value(edge),
                    edge.action_label or "",
                    str(edge.edge_id),
                ),
            )
            if best_edges:
                edge = best_edges[0]
                steps.append(
                    make_step(
                        step_order=1,
                        step_key="core_workflow",
                        phase="core_workflow",
                        goal="Open the highest-value safe workflow from the overview.",
                        screen_id=overview.screen_id,
                        recommended_action_id=str(edge.edge_id),
                        recommended_action_label=edge.action_label,
                        confidence=action_demo_value(edge),
                        evidence={"edge_id": str(edge.edge_id)},
                    )
                )
        value_node = _value_moment_node(ranked_nodes)
        if value_node is not None:
            steps.append(
                make_step(
                    step_order=len(steps),
                    step_key="value_moment",
                    phase="value_moment",
                    goal="Show the strongest visible value moment without unsafe actions.",
                    screen_id=value_node.screen_id,
                    recommended_action_id=None,
                    recommended_action_label=None,
                    confidence=screen_demo_value(value_node),
                    evidence={"screen_hash": value_node.screen_hash},
                )
            )
        steps.append(
            make_step(
                step_order=len(steps),
                step_key="q_and_a",
                phase="q_and_a",
                goal="Answer product questions using visible or retrieved evidence.",
                screen_id=None,
                recommended_action_id=None,
                recommended_action_label=None,
                confidence=0.6,
                evidence={"behavior": "retrieval_backed"},
            )
        )
        steps.append(
            make_step(
                step_order=len(steps),
                step_key="recap",
                phase="recap",
                goal="Recap verified value and ask for the next step.",
                screen_id=None,
                recommended_action_id=None,
                recommended_action_label=None,
                confidence=0.6,
                evidence={"behavior": "verified_recap"},
            )
        )
        limited = tuple(steps[: self._max_steps])
        confidence = route_confidence(tuple(step.confidence for step in limited), len(nodes))
        return GeneratedDemoRoute(
            route_id=uuid4(),
            product_id=product_id,
            route_name="Generated zero-guidance route",
            route_type="generated",
            status="draft",
            confidence=confidence,
            summary="Provisional overview, workflow, value moment, Q&A, and recap route.",
            steps=limited,
        )


def _value_moment_node(nodes: list[DemoGraphScreenNode]) -> DemoGraphScreenNode | None:
    for node in nodes:
        if node.screen_type in {"report", "dashboard_or_overview"}:
            return node
    return nodes[0] if nodes else None
