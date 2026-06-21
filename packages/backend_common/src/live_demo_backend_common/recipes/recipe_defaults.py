from __future__ import annotations

from urllib.parse import urlsplit

from live_demo_backend_common.recipes.recipe_types import DemoPhase, DemoRecipe, DemoRecipeStep

DEFAULT_NEVER_CLICK = (
    "Delete",
    "Remove",
    "Billing",
    "Invite",
    "Send",
    "Publish",
    "Upgrade",
    "Payment",
    "Account Settings",
)

DEFAULT_FALLBACK = (
    "Read the current screen, explain what can be verified, and ask whether to continue."
)


def apply_recipe_defaults(recipe: DemoRecipe, *, product_url: str | None = None) -> DemoRecipe:
    never_click = tuple(dict.fromkeys([*DEFAULT_NEVER_CLICK, *recipe.never_click]))
    allowed_domains = recipe.allowed_domains
    if not allowed_domains and product_url:
        host = urlsplit(product_url).hostname
        if host:
            allowed_domains = (host.lower().rstrip("."),)

    steps: list[DemoRecipeStep] = []
    total = len(recipe.steps)
    for step in sorted(recipe.steps, key=lambda item: item.step_order):
        phase = step.phase or _phase_for_step(step.step_order, total, step.goal)
        steps.append(
            DemoRecipeStep(
                step_order=step.step_order,
                step_key=step.step_key,
                goal=step.goal,
                phase=phase,
                screen_hint=step.screen_hint,
                click_hint=step.click_hint,
                talk_track=step.talk_track,
                allowed_actions=step.allowed_actions,
                success_criteria=step.success_criteria,
                fallback_strategy=step.fallback_strategy or DEFAULT_FALLBACK,
                max_attempts=step.max_attempts,
                required=step.required,
                confidence=step.confidence,
                source_references=step.source_references,
                step_id=step.step_id,
            )
        )
    return DemoRecipe(
        recipe_name=recipe.recipe_name,
        target_persona=recipe.target_persona,
        demo_goal=recipe.demo_goal,
        global_talk_track=recipe.global_talk_track,
        never_click=never_click,
        allowed_domains=allowed_domains,
        allowed_form_fields=recipe.allowed_form_fields,
        confirmation_required_actions=recipe.confirmation_required_actions,
        steps=tuple(steps),
        status=recipe.status,
    )


def _phase_for_step(step_order: int, total: int, goal: str) -> DemoPhase:
    lowered = goal.lower()
    if step_order == 0:
        return "OVERVIEW"
    if step_order == total - 1 or any(word in lowered for word in ("recap", "summary", "wrap")):
        return "SUMMARY"
    if any(word in lowered for word in ("question", "q&a", "answer")):
        return "Q_AND_A"
    if step_order == 1:
        return "CORE_WORKFLOW"
    return "DEEP_DIVE"
