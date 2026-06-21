from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID

from live_demo_backend_common.policy.action_policy import ActionPolicyRequest, ActionSafetyPolicy
from live_demo_backend_common.policy.policy_types import PolicyActor
from live_demo_backend_common.policy.recipe_policy import compile_recipe_policy

FIXTURES = Path(__file__).resolve().parents[5] / "policies" / "fixtures"
ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
SESSION_ID = UUID("00000000-0000-0000-0000-000000000010")
ACTOR = PolicyActor(actor_type="agent", actor_id="agent-runtime", role="agent_runtime")


def _load(name: str) -> dict[str, object]:
    return cast(dict[str, object], json.loads((FIXTURES / name).read_text()))


def _request(fixture: dict[str, object]) -> ActionPolicyRequest:
    raw = fixture["request"]
    assert isinstance(raw, dict)
    return ActionPolicyRequest(
        organization_id=ORG_ID,
        session_id=SESSION_ID,
        actor=ACTOR,
        action_type=str(raw["action_type"]),
        action_label=raw.get("action_label"),
        element_role=raw.get("element_role"),
        element_label=raw.get("element_label"),
        element_text=raw.get("element_text"),
        surrounding_text=raw.get("surrounding_text"),
        input_type=raw.get("input_type"),
        current_url=raw.get("current_url"),
        target_url=raw.get("target_url"),
        recipe_policy=compile_recipe_policy(
            {
                "allowed_domains": raw.get("allowed_domains") or [],
                "never_click": raw.get("recipe_never_click") or [],
            }
        ),
        trace_id="trace-test",
    )


def test_action_policy_shared_fixtures() -> None:
    policy = ActionSafetyPolicy()
    for fixture_file in FIXTURES.glob("action_*.json"):
        fixture = _load(fixture_file.name)
        decision = policy.evaluate(_request(fixture))
        expected = fixture["expected"]
        assert isinstance(expected, dict)
        assert decision.decision == expected["decision"]
        assert decision.risk_level == expected["risk_level"]
        assert expected["reason_code"] in decision.reason_codes
        assert 0 <= decision.risk_score <= 1


def test_recipe_never_click_fixture_blocks() -> None:
    fixture = _load("recipe_never_click_override.json")
    decision = ActionSafetyPolicy().evaluate(_request(fixture))
    assert decision.decision == "blocked"
    assert "recipe_never_click_match" in decision.reason_codes


def test_raw_javascript_and_selector_are_blocked() -> None:
    policy = ActionSafetyPolicy()
    for label, reason in [
        ("Run document.querySelector('button').click()", "javascript_forbidden"),
        ("Click css selector #danger", "raw_selector_forbidden"),
    ]:
        decision = policy.evaluate(
            ActionPolicyRequest(
                organization_id=ORG_ID,
                session_id=SESSION_ID,
                actor=ACTOR,
                action_type="click_element",
                action_label=label,
                trace_id="trace-test",
            )
        )
        assert decision.decision == "blocked"
        assert reason in decision.reason_codes
