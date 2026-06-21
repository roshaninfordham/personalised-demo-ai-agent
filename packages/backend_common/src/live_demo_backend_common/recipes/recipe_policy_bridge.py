from __future__ import annotations

from live_demo_backend_common.policy.recipe_policy import (
    CompiledRecipePolicy,
    compile_recipe_policy,
)
from live_demo_backend_common.recipes.recipe_types import DemoRecipe


def recipe_to_policy_dict(recipe: DemoRecipe) -> dict[str, object]:
    return {
        "allowed_actions": [
            {
                "action_type": action,
                "label_pattern": action,
                "risk_level_max": "medium",
            }
            for step in recipe.steps
            for action in step.allowed_actions
        ][:100],
        "never_click": list(recipe.never_click),
        "allowed_domains": list(recipe.allowed_domains),
        "allowed_form_fields": [
            {
                "field_label_pattern": item.field_label_pattern,
                "field_type": item.field_type,
                "max_chars": item.max_chars,
            }
            for item in recipe.allowed_form_fields
        ],
        "confirmation_required_actions": [
            {
                "action_type": item.action_type,
                "label_pattern": item.label_pattern,
                "reason": item.reason,
            }
            for item in recipe.confirmation_required_actions
        ],
    }


def compile_policy_for_recipe(recipe: DemoRecipe) -> CompiledRecipePolicy:
    return compile_recipe_policy(recipe_to_policy_dict(recipe))
