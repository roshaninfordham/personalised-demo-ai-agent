from uuid import UUID

from live_demo_backend_common.recipes.recipe_compiler import RecipeCompiler
from live_demo_backend_common.recipes.recipe_types import CompileRecipeRequest
from live_demo_backend_common.recipes.recipe_validator import RecipeValidator


def test_recipe_compiler_hash_is_deterministic() -> None:
    validated = RecipeValidator(product_url="https://example.com").validate(
        {
            "recipe_name": "Demo",
            "demo_goal": "Show the dashboard.",
            "steps": [{"step_order": 0, "step_key": "overview", "goal": "Show overview"}],
        }
    )
    assert validated.normalized_recipe is not None
    request = CompileRecipeRequest(
        organization_id=UUID("00000000-0000-0000-0000-000000000001"),
        product_id=UUID("00000000-0000-0000-0000-000000000020"),
        recipe_id=UUID("00000000-0000-0000-0000-000000000030"),
        normalized_recipe=validated.normalized_recipe,
        product_url="https://example.com",
        global_policy_version="v1",
        trace_id="trace",
    )

    first = RecipeCompiler().compile(request)
    second = RecipeCompiler().compile(request)

    assert first.compiled_hash == second.compiled_hash
    assert first.step_by_key["overview"].step_order == 0
