from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest

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


@pytest.mark.asyncio
async def test_core_workflow_matches_add_metric_action() -> None:
    screen = cast(dict[str, object], json.loads((FIXTURES / "screen_dashboard.json").read_text()))
    safe_actions = cast(list[dict[str, object]], screen["safe_actions"])
    compiled = _compiled()
    result = await RecipeToScreenMatcher().match_step(
        RecipeStepMatchRequest(
            organization_id=uuid4(),
            product_id=uuid4(),
            session_id=uuid4(),
            compiled_recipe=compiled,
            step_key="core_workflow",
            current_screen=ScreenContext(
                screen_id=str(screen["screen_id"]),
                screen_hash=str(screen["screen_hash"]),
                url_path=str(screen["url_path"]),
                title=str(screen["title"]),
                summary=str(screen["summary"]),
                visible_text=str(screen["visible_text"]),
                screen_type=str(screen["screen_type"]),
                confidence=cast(float, screen["confidence"]),
            ),
            safe_actions=tuple(
                SafeActionContext(
                    action_id=str(item["action_id"]),
                    action_type=str(item["action_type"]),
                    label=str(item["label"]) if item.get("label") is not None else None,
                    risk_level=str(item.get("risk_level", "unknown")),
                    score=cast(float, item.get("score", 0.0)),
                )
                for item in safe_actions
            ),
        )
    )
    assert result.decision in {"matched", "possible_match"}
    assert result.action_id == "act_add_metric"
    assert result.confidence >= 0.6


@pytest.mark.asyncio
async def test_blocked_action_not_selected() -> None:
    compiled = _compiled()
    result = await RecipeToScreenMatcher().match_step(
        RecipeStepMatchRequest(
            organization_id=uuid4(),
            product_id=uuid4(),
            session_id=uuid4(),
            compiled_recipe=compiled,
            step_key="core_workflow",
            current_screen=ScreenContext(
                screen_id="screen",
                screen_hash="hash",
                title="Dashboard",
                summary="Dashboard with metrics",
                visible_text="Delete Project",
                confidence=0.9,
            ),
            safe_actions=(
                SafeActionContext(
                    action_id="act_delete",
                    action_type="click_element",
                    label="Add Metric",
                    risk_level="blocked",
                ),
            ),
        )
    )
    assert result.decision == "blocked_by_policy"
