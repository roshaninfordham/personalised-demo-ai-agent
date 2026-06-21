from __future__ import annotations

import json
from pathlib import Path
from typing import cast
from uuid import UUID

from live_demo_backend_common.policy.action_policy import ActionPolicyRequest, ActionSafetyPolicy
from live_demo_backend_common.policy.policy_types import PolicyActor, Principal
from live_demo_backend_common.policy.rbac import RbacPolicy
from live_demo_backend_common.policy.recipe_policy import compile_recipe_policy
from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "packages" / "policies" / "fixtures"
ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
SESSION_ID = UUID("00000000-0000-0000-0000-000000000010")


def test_generated_policy_files_are_present() -> None:
    assert (
        ROOT / "packages/policies/generated/python/live_demo_policies/action_safety_rules.py"
    ).exists()
    assert (ROOT / "packages/policies/generated/typescript/src/actionSafetyRules.ts").exists()
    assert (
        ROOT / "packages/policies/generated/python/live_demo_policies/rbac_permissions.py"
    ).exists()
    assert (ROOT / "packages/policies/generated/typescript/src/rbacPermissions.ts").exists()


def test_shared_policy_fixtures_match_python_engine() -> None:
    action_policy = ActionSafetyPolicy()
    rbac = RbacPolicy()
    redaction = RedactionEngine()
    for fixture_file in sorted(FIXTURES.glob("*.json")):
        fixture = cast(dict[str, object], json.loads(fixture_file.read_text()))
        kind = fixture["kind"]
        if kind == "action_policy":
            decision = action_policy.evaluate(_action_request(fixture))
            expected = cast(dict[str, object], fixture["expected"])
            assert decision.decision == expected["decision"]
            assert expected["reason_code"] in decision.reason_codes
        elif kind == "rbac":
            principal_data = cast(dict[str, str], fixture["principal"])
            expected_rbac = cast(dict[str, bool], fixture["expected"])
            principal = Principal(
                organization_id=ORG_ID,
                actor_type="user",
                actor_id="actor",
                role=principal_data["role"],  # type: ignore[arg-type]
            )
            assert (
                rbac.has_permission(principal, cast(str, fixture["permission"]))
                is expected_rbac["allowed"]
            )
        elif kind == "redaction":
            expected = cast(dict[str, object], fixture["expected"])
            context = RedactionContext(cast(str, fixture["context"]))
            result = redaction.redact_text(cast(str, fixture["input"]), context)
            assert result.redacted_value == expected["redacted"]
        elif kind == "redaction_json":
            expected = cast(dict[str, object], fixture["expected"])
            context = RedactionContext(cast(str, fixture["context"]))
            result = redaction.redact_json(fixture["input"], context)
            for key, value in expected.items():
                assert result.redacted_value[key] == value


def _action_request(fixture: dict[str, object]) -> ActionPolicyRequest:
    raw = cast(dict[str, object], fixture["request"])
    return ActionPolicyRequest(
        organization_id=ORG_ID,
        session_id=SESSION_ID,
        actor=PolicyActor(actor_type="agent", actor_id="agent-runtime", role="agent_runtime"),
        action_type=cast(str, raw["action_type"]),
        action_label=cast(str | None, raw.get("action_label")),
        element_role=cast(str | None, raw.get("element_role")),
        element_label=cast(str | None, raw.get("element_label")),
        element_text=cast(str | None, raw.get("element_text")),
        surrounding_text=cast(str | None, raw.get("surrounding_text")),
        input_type=cast(str | None, raw.get("input_type")),
        current_url=cast(str | None, raw.get("current_url")),
        target_url=cast(str | None, raw.get("target_url")),
        recipe_policy=compile_recipe_policy(
            {
                "allowed_domains": raw.get("allowed_domains") or [],
                "never_click": raw.get("recipe_never_click") or [],
            }
        ),
        trace_id="trace-fixture",
    )
