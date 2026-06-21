from __future__ import annotations

from uuid import UUID

import pytest

from live_demo_backend_common.policy.policy_errors import PermissionDeniedError
from live_demo_backend_common.policy.policy_types import Principal
from live_demo_backend_common.policy.rbac import RbacPolicy

ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


def principal(role: str) -> Principal:
    return Principal(
        organization_id=ORG_ID,
        actor_type="user" if role != "agent_runtime" else "agent",
        actor_id="actor",
        role=role,  # type: ignore[arg-type]
    )


def test_owner_has_all_permissions() -> None:
    assert RbacPolicy().has_permission(principal("owner"), "crm:export")


def test_role_permissions() -> None:
    policy = RbacPolicy()
    assert policy.has_permission(principal("admin"), "recipe:delete")
    assert policy.has_permission(principal("demo_builder"), "recipe:activate")
    assert not policy.has_permission(principal("demo_builder"), "user:manage")
    assert policy.has_permission(principal("viewer"), "recipe:read")
    assert not policy.has_permission(principal("viewer"), "recipe:update")
    assert policy.has_permission(principal("agent_runtime"), "browser:execute_medium")
    assert not policy.has_permission(principal("agent_runtime"), "crm:export")


def test_missing_permission_raises_deterministic_error() -> None:
    with pytest.raises(PermissionDeniedError) as exc:
        RbacPolicy().require_permission(principal("viewer"), "recipe:activate")
    assert exc.value.code == "missing_required_permission"

