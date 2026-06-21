"""Route scoring functions."""

from __future__ import annotations

from live_demo_learner_worker.demo_graph.graph_types import DemoGraphActionEdge, DemoGraphScreenNode


def screen_demo_value(node: DemoGraphScreenNode) -> float:
    screen_type_value = {
        "dashboard_or_overview": 1.0,
        "report": 0.9,
        "form": 0.8,
        "settings_or_risky": 0.2,
    }.get(node.screen_type or "", 0.4)
    feature_density = min(1.0, len(node.features) / 8)
    safe_action_count_score = 0.5
    category_relevance = 1.0 if node.screen_type in {"dashboard_or_overview", "report"} else 0.5
    novelty = 1.0
    risk_score = 1.0 if node.risk_level in {"high", "blocked"} else 0.1
    return round(
        max(
            0.0,
            0.25 * screen_type_value
            + 0.20 * feature_density
            + 0.15 * safe_action_count_score
            + 0.15 * category_relevance
            + 0.15 * node.confidence
            + 0.10 * novelty
            - 0.30 * risk_score,
        ),
        4,
    )


def action_demo_value(edge: DemoGraphActionEdge) -> float:
    label = (edge.action_label or "").lower()
    label_relevance = (
        1.0 if any(word in label for word in ("dashboard", "report", "metric", "create")) else 0.4
    )
    leads_to_new_screen = 1.0 if edge.to_screen_id is not None else 0.2
    recipe_like_value = 1.0 if edge.action_type in {"click_element", "scroll", "go_back"} else 0.5
    visibility = 1.0
    category_relevance = label_relevance
    risk_score = {"low": 0.1, "medium": 0.5, "high": 0.9, "blocked": 1.0}.get(edge.risk_level, 0.6)
    return round(
        max(
            0.0,
            0.25 * label_relevance
            + 0.20 * edge.confidence
            + 0.15 * leads_to_new_screen
            + 0.15 * recipe_like_value
            + 0.10 * visibility
            + 0.15 * category_relevance
            - 0.35 * risk_score,
        ),
        4,
    )


def route_confidence(step_confidences: tuple[float, ...], observed_screen_count: int) -> float:
    if not step_confidences:
        return 0.0
    graph_coverage_factor = min(1.0, observed_screen_count / 3)
    safety_factor = 1.0
    return round(
        (sum(step_confidences) / len(step_confidences)) * graph_coverage_factor * safety_factor, 3
    )
