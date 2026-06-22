from live_demo_backend_common.recipes.recipe_validator import RecipeValidator


def test_recipe_validator_accepts_fixture_shape() -> None:
    result = RecipeValidator(product_url="https://example.com").validate(
        {
            "recipe_name": "Demo",
            "demo_goal": "Show the dashboard.",
            "steps": [{"step_order": 0, "step_key": "overview", "goal": "Show overview"}],
        }
    )

    assert result.valid is True
    assert result.normalized_recipe is not None
