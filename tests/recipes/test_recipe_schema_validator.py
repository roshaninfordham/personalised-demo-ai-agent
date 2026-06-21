from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from live_demo_backend_common.recipes.recipe_types import RecipeValidationResult
from live_demo_backend_common.recipes.recipe_validator import RecipeValidator

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, object]:
    return cast(dict[str, object], json.loads((FIXTURES / name).read_text()))


def codes(result: RecipeValidationResult) -> set[str]:
    return {issue.code for issue in result.errors}


def test_minimal_valid_recipe_passes_with_defaults() -> None:
    result = RecipeValidator(product_url="https://example.com").validate(
        load_fixture("valid_minimal_recipe.json")
    )
    assert result.valid
    assert result.normalized_recipe is not None
    assert "Delete" in result.normalized_recipe.never_click
    assert "Payment" in result.normalized_recipe.never_click
    assert result.normalized_recipe.allowed_domains == ("example.com",)


def test_full_valid_recipe_passes() -> None:
    result = RecipeValidator(product_url="https://example.com").validate(
        load_fixture("valid_full_recipe.json")
    )
    assert result.valid, [issue.code for issue in result.errors]


def test_duplicate_step_order_fails() -> None:
    result = RecipeValidator(product_url="https://example.com").validate(
        load_fixture("invalid_duplicate_step_order.json")
    )
    assert not result.valid
    assert {"duplicate_step_order", "step_order_not_contiguous"} <= codes(result)


def test_destructive_allowed_action_fails() -> None:
    result = RecipeValidator(product_url="https://example.com").validate(
        load_fixture("invalid_destructive_action.json")
    )
    assert not result.valid
    assert "destructive_action_forbidden" in codes(result)


def test_raw_selector_in_click_hint_fails() -> None:
    result = RecipeValidator(product_url="https://example.com").validate(
        load_fixture("invalid_raw_selector.json")
    )
    assert not result.valid
    assert "raw_selector_forbidden" in codes(result)


def test_javascript_in_fallback_fails() -> None:
    payload = load_fixture("valid_minimal_recipe.json")
    steps = cast(list[dict[str, object]], payload["steps"])
    steps[0]["fallback_strategy"] = "Run document.querySelector('#x').click()"
    result = RecipeValidator(product_url="https://example.com").validate(payload)
    assert not result.valid
    assert "javascript_forbidden" in codes(result)


def test_sensitive_form_field_fails() -> None:
    payload = load_fixture("valid_minimal_recipe.json")
    payload["allowed_form_fields"] = [
        {"field_label_pattern": "API Key", "field_type": "text", "max_chars": 120}
    ]
    result = RecipeValidator(product_url="https://example.com").validate(payload)
    assert not result.valid
    assert "sensitive_form_field_forbidden" in codes(result)


def test_private_allowed_domain_fails() -> None:
    payload = load_fixture("valid_minimal_recipe.json")
    payload["allowed_domains"] = ["localhost"]
    result = RecipeValidator(product_url="https://example.com").validate(payload)
    assert not result.valid
    assert "private_domain_forbidden" in codes(result)
