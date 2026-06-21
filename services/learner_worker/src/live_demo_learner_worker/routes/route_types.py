"""Generated route data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class GeneratedRouteStep:
    route_step_id: UUID
    step_order: int
    step_key: str
    phase: str
    goal: str
    screen_id: UUID | None
    recommended_action_id: str | None
    recommended_action_label: str | None
    talk_track: str | None
    fallback_strategy: str | None
    confidence: float
    evidence: dict[str, object]


@dataclass(frozen=True, slots=True)
class GeneratedDemoRoute:
    route_id: UUID
    product_id: UUID
    route_name: str
    route_type: str
    status: str
    confidence: float
    summary: str
    steps: tuple[GeneratedRouteStep, ...] = field(default_factory=tuple)


def make_step(
    *,
    step_order: int,
    step_key: str,
    phase: str,
    goal: str,
    screen_id: UUID | None,
    recommended_action_id: str | None,
    recommended_action_label: str | None,
    confidence: float,
    evidence: dict[str, object] | None = None,
) -> GeneratedRouteStep:
    return GeneratedRouteStep(
        route_step_id=uuid4(),
        step_order=step_order,
        step_key=step_key,
        phase=phase,
        goal=goal,
        screen_id=screen_id,
        recommended_action_id=recommended_action_id,
        recommended_action_label=recommended_action_label,
        talk_track=None,
        fallback_strategy="Re-read the current screen and continue with a grounded explanation.",
        confidence=round(confidence, 3),
        evidence=evidence or {},
    )
