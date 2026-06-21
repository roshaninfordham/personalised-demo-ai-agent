"""Generated route validation."""

from __future__ import annotations

from live_demo_learner_worker.routes.route_types import GeneratedDemoRoute


def route_is_safe(route: GeneratedDemoRoute) -> bool:
    return all(step.confidence >= 0.0 and step.goal for step in route.steps)
