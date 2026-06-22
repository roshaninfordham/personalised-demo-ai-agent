from __future__ import annotations

import statistics
import time
from uuid import UUID

from live_demo_backend_common.policy.action_policy import (
    ActionPolicyRequest,
    ActionSafetyPolicy,
)
from live_demo_backend_common.policy.policy_types import PolicyActor
from live_demo_backend_common.policy.recipe_policy import (
    CompiledRecipePolicy,
    compile_recipe_policy,
)

ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
SESSION_ID = UUID("00000000-0000-0000-0000-000000000010")
ACTOR = PolicyActor(actor_type="agent", actor_id="agent", role="demo_builder")


def test_blocked_actions_fail_closed() -> None:
    policy = ActionSafetyPolicy()
    cases = [
        ("Delete Project", "blocked_destructive_action"),
        ("Remove user", "blocked_destructive_action"),
        ("Billing", "payment_billing_blocked"),
        ("Payment checkout", "payment_billing_blocked"),
        ("Purchase upgrade", "payment_billing_blocked"),
        ("Account Settings", "account_settings_sensitive_context_blocked"),
        ("document.querySelector('#delete').click()", "javascript_forbidden"),
        ("click #settings-button", "raw_selector_forbidden"),
        ("xpath=//button", "raw_selector_forbidden"),
    ]

    for label, expected_reason in cases:
        surrounding = (
            "security controls" if label == "Account Settings" else "security billing controls"
        )
        decision = policy.evaluate(
            _request(
                action_label=label,
                element_label=label,
                surrounding_text=surrounding,
            )
        )

        assert decision.decision == "blocked", label
        assert decision.risk_level == "blocked", label
        assert decision.risk_score >= 0.85, label
        assert expected_reason in decision.reason_codes, decision.reason_codes


def test_domain_and_sensitive_field_blocks() -> None:
    policy = ActionSafetyPolicy()

    external = policy.evaluate(
        _request(action_label="Open docs", target_url="https://outside.example.net/page")
    )
    private = policy.evaluate(
        _request(action_label="Open local admin", target_url="http://127.0.0.1:8080")
    )
    credential_field = policy.evaluate(
        _request(
            action_type="type_into_element",
            action_label="Type value",
            element_role="input",
            element_label="API Key",
            input_type="text",
        )
    )

    assert external.decision == "blocked"
    assert "external_navigation_blocked" in external.reason_codes
    assert private.decision == "blocked"
    assert credential_field.decision == "blocked"
    assert "sensitive_field_blocked" in credential_field.reason_codes


def test_high_risk_actions_require_confirmation() -> None:
    policy = ActionSafetyPolicy()
    for label in ["Invite User", "Send email", "Publish", "Export sensitive data"]:
        decision = policy.evaluate(_request(action_label=label, element_label=label))

        assert decision.decision == "confirmation_required"
        assert decision.risk_level == "high"
        assert decision.requires_confirmation is True


def test_recipe_permissions_can_only_make_policy_stricter() -> None:
    recipe = compile_recipe_policy(
        {
            "never_click": ["Reports"],
            "allowed_domains": ["example.com", "*.example.com"],
            "allowed_actions": [
                {"action_type": "click_element", "label_pattern": "Add Metric"},
            ],
            "allowed_form_fields": [
                {"field_label_pattern": "Metric Name", "field_type": "text", "max_chars": 80},
            ],
            "confirmation_required_actions": [
                {
                    "action_type": "click_element",
                    "label_pattern": "Save",
                    "reason": "Changing fixture data",
                }
            ],
        }
    )
    policy = ActionSafetyPolicy()

    never_click = policy.evaluate(_request(action_label="Reports", recipe_policy=recipe))
    allowed_medium = policy.evaluate(_request(action_label="Add Metric", recipe_policy=recipe))
    exact_domain = policy.evaluate(
        _request(
            action_label="Add Metric",
            target_url="https://example.com/dashboard",
            recipe_policy=recipe,
        )
    )
    wildcard_domain = policy.evaluate(
        _request(
            action_label="Add Metric",
            target_url="https://app.example.com/dashboard",
            recipe_policy=recipe,
        )
    )
    forced_confirmation = policy.evaluate(_request(action_label="Save", recipe_policy=recipe))
    global_block = policy.evaluate(_request(action_label="Billing", recipe_policy=recipe))
    payment_field = policy.evaluate(
        _request(
            action_type="type_into_element",
            action_label="Type card",
            element_role="input",
            element_label="Card Number",
            input_type="text",
            recipe_policy=recipe,
        )
    )

    assert never_click.decision == "blocked"
    assert allowed_medium.decision == "allowed"
    assert exact_domain.decision == "allowed"
    assert wildcard_domain.decision == "allowed"
    assert forced_confirmation.decision == "confirmation_required"
    assert global_block.decision == "blocked"
    assert payment_field.decision == "blocked"
    assert recipe.allows_form_field("Metric Name", "text") is True


def test_allowed_safe_actions_remain_executable() -> None:
    policy = ActionSafetyPolicy()
    cases = [
        _request(action_type="read_current_screen", action_label="Read current screen"),
        _request(action_type="highlight_element", action_label="Highlight Dashboard"),
        _request(action_type="scroll", action_label="Scroll"),
        _request(action_type="go_back", action_label="Back"),
        _request(action_type="click_element", action_label="Dashboard"),
        _request(action_type="click_element", action_label="Reports"),
        _request(action_type="click_element", action_label="Filter last 7 days"),
        _request(
            action_type="type_into_element", action_label="Metric Name", element_label="Metric Name"
        ),
    ]

    for request in cases:
        decision = policy.evaluate(request)
        assert decision.decision == "allowed", request.action_label
        assert decision.risk_level in {"low", "medium"}, request.action_label
        assert decision.reason_codes


def test_policy_property_cases_are_deterministic() -> None:
    policy = ActionSafetyPolicy()
    for label in ["delete", "Delete item", "safe delete copy", "billing", "Open billing page"]:
        assert policy.evaluate(_request(action_label=label)).decision == "blocked"

    assert (
        policy.evaluate(_request(action_label="Open", target_url="https://unlisted.test")).decision
        == "blocked"
    )


def test_policy_evaluation_p50_under_two_ms_for_bounded_rules() -> None:
    policy = ActionSafetyPolicy()
    requests = [_request(action_label=f"Open Dashboard {index}") for index in range(1000)]
    durations: list[float] = []

    for request in requests:
        started = time.perf_counter_ns()
        policy.evaluate(request)
        durations.append((time.perf_counter_ns() - started) / 1_000_000)

    assert statistics.median(durations) <= 2.0


def _request(
    *,
    action_type: str = "click_element",
    action_label: str = "Open Dashboard",
    element_role: str | None = "button",
    element_label: str | None = None,
    surrounding_text: str | None = None,
    input_type: str | None = None,
    target_url: str | None = None,
    recipe_policy: CompiledRecipePolicy | None = None,
) -> ActionPolicyRequest:
    return ActionPolicyRequest(
        organization_id=ORG_ID,
        session_id=SESSION_ID,
        actor=ACTOR,
        action_type=action_type,
        action_label=action_label,
        element_role=element_role,
        element_label=element_label or action_label,
        surrounding_text=surrounding_text,
        input_type=input_type,
        target_url=target_url,
        recipe_policy=recipe_policy,
    )
