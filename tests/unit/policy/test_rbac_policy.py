from uuid import UUID

import pytest

from live_demo_backend_common.policy.policy_errors import PermissionDeniedError
from live_demo_backend_common.policy.policy_types import Principal
from live_demo_backend_common.policy.rbac import RbacPolicy


def test_rbac_policy_uses_bounded_set_membership() -> None:
    policy = RbacPolicy()
    owner = Principal(
        organization_id=UUID("00000000-0000-0000-0000-000000000001"),
        actor_type="user",
        actor_id="owner",
        role="owner",
    )
    viewer = Principal(
        organization_id=owner.organization_id,
        actor_type="user",
        actor_id="viewer",
        role="viewer",
    )

    assert policy.has_permission(owner, "session:start") is True
    assert policy.has_permission(viewer, "session:start") is False
    with pytest.raises(PermissionDeniedError):
        policy.require_permission(viewer, "session:start")
