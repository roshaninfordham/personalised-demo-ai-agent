from __future__ import annotations

import json
import time
from pathlib import Path
from uuid import uuid4

from live_demo_backend_common.recipes.recipe_compiler import RecipeCompiler
from live_demo_backend_common.recipes.recipe_to_screen_matcher import RecipeToScreenMatcher
from live_demo_backend_common.recipes.recipe_types import (
    CompiledRecipe,
    CompileRecipeRequest,
    RecipeStepMatchRequest,
    SafeActionContext,
    ScreenContext,
)
from live_demo_backend_common.recipes.recipe_validator import RecipeValidator

FIXTURES = Path(__file__).parent / "fixtures"


def _compiled() -> CompiledRecipe:
    raw = json.loads((FIXTURES / "valid_full_recipe.json").read_text())
    validation = RecipeValidator(product_url="https://example.com").validate(raw)
    assert validation.valid and validation.normalized_recipe is not None
    return RecipeCompiler().compile(
        CompileRecipeRequest(
            organization_id=uuid4(),
            product_id=uuid4(),
            recipe_id=uuid4(),
            normalized_recipe=validation.normalized_recipe,
            product_url="https://example.com",
        )
    )


async def test_compile_and_match_hot_path_budget_is_bounded() -> None:
    start = time.perf_counter()
    compiled = _compiled()
    compile_ms = (time.perf_counter() - start) * 1000
    assert compile_ms < 75

    request = RecipeStepMatchRequest(
        organization_id=uuid4(),
        product_id=uuid4(),
        session_id=uuid4(),
        compiled_recipe=compiled,
        step_key="core_workflow",
        current_screen=ScreenContext(
            screen_id="screen_dashboard",
            screen_hash="hash_dashboard",
            title="Dashboard",
            summary="Revenue metrics dashboard with Add Metric action.",
            visible_text="Dashboard Revenue Metrics Add Metric Reports",
            screen_type="dashboard",
            confidence=0.9,
        ),
        safe_actions=(
            SafeActionContext(
                action_id="act_add_metric",
                action_type="click_element",
                label="Add Metric",
                risk_level="low",
                score=0.92,
            ),
        ),
    )
    start = time.perf_counter()
    result = await RecipeToScreenMatcher().match_step(request)
    match_ms = (time.perf_counter() - start) * 1000
    assert result.decision in {"matched", "possible_match"}
    assert match_ms < 50
