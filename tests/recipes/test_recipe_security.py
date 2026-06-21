from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID

from live_demo_backend_common.recipes.recipe_compiler import RecipeCompiler
from live_demo_backend_common.recipes.recipe_types import CompileRecipeRequest
from live_demo_backend_common.recipes.recipe_validator import RecipeValidator

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> dict[str, object]:
    return cast(dict[str, object], json.loads((FIXTURES / name).read_text()))


def test_recipe_cannot_bypass_global_hard_blocks_with_allowed_actions() -> None:
    payload = _fixture("valid_minimal_recipe.json")
    payload["never_click"] = []
    steps = cast(list[dict[str, object]], payload["steps"])
    steps[0]["allowed_actions"] = ["click_element", "Delete Project"]
    result = RecipeValidator(product_url="https://example.com").validate(payload)
    assert not result.valid
    assert {issue.code for issue in result.errors} >= {"destructive_action_forbidden"}


def test_compiled_recipe_contains_no_raw_selector_or_javascript() -> None:
    payload = _fixture("valid_full_recipe.json")
    result = RecipeValidator(product_url="https://example.com").validate(payload)
    assert result.valid and result.normalized_recipe is not None
    compiled = RecipeCompiler().compile(
        CompileRecipeRequest(
            organization_id=UUID("00000000-0000-0000-0000-000000000001"),
            product_id=UUID("00000000-0000-0000-0000-000000000020"),
            recipe_id=UUID("00000000-0000-0000-0000-000000000030"),
            normalized_recipe=result.normalized_recipe,
            product_url="https://example.com",
        )
    )
    compiled_text = json.dumps(compiled.payload, sort_keys=True)
    assert "querySelector" not in compiled_text
    assert "document." not in compiled_text
    assert "#dashboard" not in compiled_text
