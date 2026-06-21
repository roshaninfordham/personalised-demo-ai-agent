from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from live_demo_backend_common.recipes.recipe_compiler import RecipeCompiler
from live_demo_backend_common.recipes.recipe_types import CompiledRecipe, CompileRecipeRequest
from live_demo_backend_common.recipes.recipe_validator import RecipeValidator

FIXTURES = Path(__file__).parent / "fixtures"


def compiled_recipe() -> tuple[CompiledRecipe, CompileRecipeRequest]:
    raw = json.loads((FIXTURES / "valid_full_recipe.json").read_text())
    validation = RecipeValidator(product_url="https://example.com").validate(raw)
    assert validation.valid and validation.normalized_recipe is not None
    request = CompileRecipeRequest(
        organization_id=uuid4(),
        product_id=uuid4(),
        recipe_id=uuid4(),
        normalized_recipe=validation.normalized_recipe,
        product_url="https://example.com",
    )
    return RecipeCompiler().compile(request), request


def test_compiled_hash_is_deterministic() -> None:
    first, request = compiled_recipe()
    second = RecipeCompiler().compile(request)
    assert first.compiled_hash == second.compiled_hash
    assert first.recipe_hash == second.recipe_hash


def test_step_lookup_and_policy_payloads_exist() -> None:
    compiled, _ = compiled_recipe()
    assert compiled.step_by_key["overview"].step_order == 0
    assert compiled.steps_by_order[1].step_key == "core_workflow"
    assert "Delete" in compiled.safety_policy.never_click
    assert compiled.domain_policy.exact_domains == ("example.com",)
    assert compiled.payload["context_payload"]["steps"][0]["step_key"] == "overview"
