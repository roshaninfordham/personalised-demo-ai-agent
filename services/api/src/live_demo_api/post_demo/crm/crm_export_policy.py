"""CRM export policy."""

from __future__ import annotations

from live_demo_api.security import Principal


def can_export_crm(principal: Principal) -> bool:
    return principal.role in {"owner", "admin"}
