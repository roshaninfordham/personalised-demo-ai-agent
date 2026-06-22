from live_demo_backend_common.policy.recipe_policy import compile_recipe_policy


def test_recipe_policy_compiles_matchers_and_permissions() -> None:
    policy = compile_recipe_policy(
        {
            "never_click": ["Billing"],
            "allowed_domains": ["example.com", "*.example.com"],
            "allowed_actions": [{"action_type": "click_element", "label_pattern": "Reports"}],
            "allowed_form_fields": [
                {"field_label_pattern": "Metric Name", "field_type": "text", "max_chars": 80}
            ],
            "confirmation_required_actions": [
                {"action_type": "click_element", "label_pattern": "Save", "reason": "writes data"}
            ],
        }
    )

    assert policy.never_click_matcher.match("Open Billing")
    assert policy.allows_action("click_element", "Reports") is True
    assert policy.allows_action("click_element", "Billing") is False
    assert policy.allows_form_field("Metric Name", "text") is True
    assert policy.requires_confirmation("click_element", "Save") is True
