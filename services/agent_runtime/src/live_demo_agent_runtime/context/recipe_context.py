"""Recipe context helpers."""

from typing import Any

from live_demo_agent_runtime.context.context_budget import truncate_text
from live_demo_agent_runtime.context.context_types import RecipeStepContext


def active_compiled_recipe_context(
    compiled_payload: dict[str, Any],
    *,
    active_step_key: str | None,
    progress_ratio: float,
) -> dict[str, Any]:
    context_payload = compiled_payload.get("context_payload")
    if not isinstance(context_payload, dict):
        return {}
    steps = context_payload.get("steps")
    step_items = steps if isinstance(steps, list) else []
    active_index = next(
        (
            index
            for index, step in enumerate(step_items)
            if isinstance(step, dict) and step.get("step_key") == active_step_key
        ),
        0,
    )
    active = step_items[active_index] if step_items else None
    previous_step = step_items[active_index - 1] if active_index > 0 else None
    next_step = step_items[active_index + 1] if active_index + 1 < len(step_items) else None
    return {
        "recipe_name": context_payload.get("recipe_name"),
        "target_persona": context_payload.get("target_persona"),
        "demo_goal": context_payload.get("demo_goal"),
        "active_step": active,
        "previous_step": previous_step,
        "next_step": next_step,
        "never_click": context_payload.get("never_click", []),
        "progress_ratio": progress_ratio,
    }


def clamp_recipe_step(step: RecipeStepContext | None, max_chars: int) -> RecipeStepContext | None:
    if step is None:
        return None
    goal, _ = truncate_text(step.goal, max_chars)
    talk_track, _ = truncate_text(step.talk_track or "", max_chars)
    return RecipeStepContext(
        step_key=step.step_key,
        goal=goal,
        screen_hint=step.screen_hint,
        click_hint=step.click_hint,
        talk_track=talk_track or None,
        allowed_actions=step.allowed_actions,
        success_criteria=step.success_criteria,
        fallback_strategy=step.fallback_strategy,
    )
