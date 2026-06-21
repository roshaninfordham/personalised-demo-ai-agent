from __future__ import annotations

from pathlib import Path

from live_demo_backend_common.recipes.recipe_generation import (
    DeterministicGuidanceExtractor,
    RecipeGenerationInput,
    TextGuidanceRecipeGenerator,
)
from live_demo_backend_common.recipes.recipe_validator import RecipeValidator

FIXTURES = Path(__file__).parent / "fixtures"


def test_founder_metrics_guidance_generates_valid_draft_recipe() -> None:
    guidance = (FIXTURES / "guidance_founder_metrics.txt").read_text()
    generator = TextGuidanceRecipeGenerator(
        validator=RecipeValidator(product_url="https://example.com")
    )
    recipe = generator.generate_fallback(
        RecipeGenerationInput(
            organization_id="org",
            product_id="product",
            product_name="Metric Master",
            product_url="https://example.com",
            text_guidance=guidance,
            target_persona="founder",
        )
    )
    validation = RecipeValidator(product_url="https://example.com").validate(recipe)
    assert validation.valid, [issue.code for issue in validation.errors]
    assert recipe["target_persona"] == "founder"
    assert "Billing" in recipe["never_click"]
    assert recipe["steps"][0]["step_key"] == "overview"
    assert recipe["steps"][-1]["step_key"] == "recap"


def test_guidance_extractor_redacts_and_extracts_avoid_items() -> None:
    extraction = DeterministicGuidanceExtractor().extract(
        "Show dashboard then reports. Avoid billing and delete. Contact alice@example.com.",
        "founder",
    )
    assert extraction.persona == "founder"
    assert extraction.redaction_applied
    assert "[REDACTED_EMAIL]" in extraction.redacted_guidance
    assert any("billing" in item.lower() for item in extraction.avoid_items)
