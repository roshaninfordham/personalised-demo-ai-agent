"""FastAPI RBAC dependencies backed by the shared policy package."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from live_demo_api.dependencies import get_current_principal
from live_demo_api.errors import ForbiddenError
from live_demo_api.security import Principal
from live_demo_api.services.audit_service import to_policy_principal
from live_demo_backend_common.policy.policy_errors import PermissionDeniedError
from live_demo_backend_common.policy.rbac import RbacPolicy

_RBAC = RbacPolicy()


def require_permission(permission: str) -> Callable[[Principal], Principal]:
    def dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        try:
            _RBAC.require_permission(to_policy_principal(principal), permission)
        except PermissionDeniedError as exc:
            raise ForbiddenError(
                "Missing required permission.",
                code="missing_required_permission",
                details={"permission": permission},
            ) from exc
        return principal

    return dependency


def has_permission(principal: Principal, permission: str) -> bool:
    return _RBAC.has_permission(to_policy_principal(principal), permission)
