from __future__ import annotations

from typing import cast

from live_demo_backend_common.policy.policy_errors import PermissionDeniedError
from live_demo_backend_common.policy.policy_types import Principal
from live_demo_policies.rbac_permissions import RBAC_PERMISSIONS


class RbacPolicy:
    def __init__(self, role_permissions: dict[str, list[str]] | None = None) -> None:
        raw = role_permissions or cast(dict[str, list[str]], RBAC_PERMISSIONS["roles"])
        self._role_permissions: dict[str, frozenset[str]] = {
            role: frozenset(permissions) for role, permissions in raw.items()
        }

    def has_permission(self, principal: Principal, permission: str) -> bool:
        permissions = self._role_permissions.get(principal.role, frozenset())
        if "*" in permissions or permission in permissions or permission in principal.scopes:
            return True
        resource = permission.split(":", 1)[0]
        return f"{resource}:*" in permissions or f"{resource}:*" in principal.scopes

    def require_permission(self, principal: Principal, permission: str) -> None:
        if not self.has_permission(principal, permission):
            raise PermissionDeniedError(permission)
