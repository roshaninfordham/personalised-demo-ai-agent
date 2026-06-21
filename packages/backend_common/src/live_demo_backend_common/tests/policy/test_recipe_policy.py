from __future__ import annotations

from live_demo_backend_common.policy.recipe_policy import compile_recipe_policy


def test_recipe_policy_compiles_deterministically() -> None:
    raw = {
        "allowed_actions": [
            {
                "action_type": "click_element",
                "label_pattern": "Add Metric",
                "risk_level_max": "medium",
            }
        ],
        "never_click": ["Delete", "Billing"],
        "allowed_domains": ["example.com", "*.example.com"],
        "allowed_form_fields": [
            {"field_label_pattern": "Metric Name", "field_type": "text", "max_chars": 120}
        ],
        "confirmation_required_actions": [
            {
                "action_type": "type_into_element",
                "label_pattern": "Save",
                "reason": "Mutates demo data",
            }
        ],
    }
    first = compile_recipe_policy(raw)
    second = compile_recipe_policy(raw)
    assert first.allowed_actions == second.allowed_actions
    assert first.never_click == second.never_click
    assert first.allowed_domains == second.allowed_domains
    assert first.allowed_form_fields == second.allowed_form_fields
    assert first.confirmation_required_actions == second.confirmation_required_actions
    assert first.allows_action("click_element", "Add Metric")
    assert not first.allows_action("click_element", "Delete Metric")
    assert first.never_click_matcher.match("Delete project")
    assert first.allows_form_field("Metric Name", "text")
    assert first.requires_confirmation("type_into_element", "Save")
