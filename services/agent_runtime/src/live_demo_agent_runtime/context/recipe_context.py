"""Recipe context helpers."""

from live_demo_agent_runtime.context.context_budget import truncate_text
from live_demo_agent_runtime.context.context_types import RecipeStepContext


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
