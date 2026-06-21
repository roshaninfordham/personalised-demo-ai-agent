from __future__ import annotations

from uuid import UUID

import pytest

from live_demo_api.errors import ForbiddenError
from live_demo_api.rbac_dependencies import has_permission, require_permission
from live_demo_api.security import Principal

ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
USER_ID = UUID("00000000-0000-0000-0000-000000000002")


def principal(role: str) -> Principal:
    return Principal(
        organization_id=ORG_ID,
        user_id=USER_ID,
        role=role,
        actor_type="user",
    )


def test_api_rbac_dependency_allows_owner() -> None:
    dependency = require_permission("crm:export")
    assert dependency(principal("owner")).role == "owner"


def test_api_rbac_dependency_rejects_viewer_mutation() -> None:
    dependency = require_permission("recipe:activate")
    with pytest.raises(ForbiddenError) as exc:
        dependency(principal("viewer"))
    assert exc.value.code == "missing_required_permission"


def test_api_rbac_agent_runtime_scope() -> None:
    agent = Principal(
        organization_id=ORG_ID,
        user_id=None,
        role="agent_runtime",
        actor_type="agent",
    )
    assert has_permission(agent, "browser:execute_medium")
    assert not has_permission(agent, "crm:export")

