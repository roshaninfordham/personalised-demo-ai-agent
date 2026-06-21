"""Static Phase 12 prewarm dependency plan."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PrewarmPlanStep:
    name: str
    depends_on: tuple[str, ...]
    required: bool
    timeout_ms: int


def build_default_prewarm_plan() -> tuple[PrewarmPlanStep, ...]:
    return (
        PrewarmPlanStep("load_session", (), True, 500),
        PrewarmPlanStep("compile_recipe", ("load_session",), False, 3000),
        PrewarmPlanStep("create_browser_session", ("load_session",), True, 12000),
        PrewarmPlanStep("navigate_browser", ("create_browser_session",), True, 12000),
        PrewarmPlanStep("read_first_screen", ("navigate_browser",), True, 3000),
        PrewarmPlanStep("create_voice_session", ("load_session",), False, 5000),
        PrewarmPlanStep("get_join_config", ("create_voice_session",), False, 1000),
        PrewarmPlanStep("warm_providers", ("load_session",), False, 3000),
        PrewarmPlanStep("enqueue_learner", ("load_session",), False, 1000),
        PrewarmPlanStep("compute_readiness", ("read_first_screen",), True, 100),
    )


def validate_prewarm_plan(plan: tuple[PrewarmPlanStep, ...]) -> bool:
    names = {step.name for step in plan}
    return all(dependency in names for step in plan for dependency in step.depends_on)
