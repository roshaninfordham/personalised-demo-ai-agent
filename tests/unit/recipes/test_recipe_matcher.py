from uuid import UUID

import pytest

from live_demo_backend_common.recipes.recipe_compiler import RecipeCompiler
from live_demo_backend_common.recipes.recipe_to_screen_matcher import RecipeToScreenMatcher
from live_demo_backend_common.recipes.recipe_types import (
    CompileRecipeRequest,
    RecipeStepMatchRequest,
    SafeActionContext,
    ScreenContext,
)
from live_demo_backend_common.recipes.recipe_validator import RecipeValidator


@pytest.mark.asyncio
async def test_recipe_matcher_matches_dashboard_step_to_safe_action() -> None:
    validated = RecipeValidator(product_url="https://example.com").validate(
        {
            "recipe_name": "Demo",
            "demo_goal": "Show the dashboard.",
            "steps": [
                {
                    "step_order": 0,
                    "step_key": "overview",
                    "goal": "Show dashboard overview",
                    "screen_hint": "dashboard metrics",
                    "click_hint": "Dashboard",
                    "allowed_actions": ["highlight_element"],
                }
            ],
        }
    )
    assert validated.normalized_recipe is not None
    compiled = RecipeCompiler().compile(
        CompileRecipeRequest(
            organization_id=UUID("00000000-0000-0000-0000-000000000001"),
            product_id=UUID("00000000-0000-0000-0000-000000000020"),
            recipe_id=UUID("00000000-0000-0000-0000-000000000030"),
            normalized_recipe=validated.normalized_recipe,
            product_url="https://example.com",
        )
    )

    result = await RecipeToScreenMatcher().match_step(
        RecipeStepMatchRequest(
            organization_id=UUID("00000000-0000-0000-0000-000000000001"),
            product_id=UUID("00000000-0000-0000-0000-000000000020"),
            session_id=UUID("00000000-0000-0000-0000-000000000010"),
            compiled_recipe=compiled,
            step_key="overview",
            current_screen=ScreenContext(
                screen_id="screen_dashboard",
                screen_hash="hash",
                url_path="/",
                title="Dashboard",
                summary="Dashboard metrics overview",
                visible_text="Dashboard Revenue Metrics",
                confidence=0.9,
            ),
            safe_actions=(
                SafeActionContext(
                    action_id="act_dashboard",
                    action_type="highlight_element",
                    label="Dashboard",
                    risk_level="low",
                    score=0.95,
                ),
            ),
            candidate_screens=(),
            trace_id="trace",
        )
    )

    assert result.decision in {"matched", "possible_match"}
    assert result.action_id == "act_dashboard"
