"""Category-to-persona inference."""

from __future__ import annotations

PERSONAS_BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "analytics_dashboard": ("founder", "operator", "analytics_leader"),
    "crm_sales": ("sales", "executive", "customer_success"),
    "marketing_automation": ("marketing", "growth", "operator"),
    "developer_tool": ("engineering", "product"),
    "security_compliance": ("security", "engineering", "executive"),
    "operations_workflow": ("operator", "customer_success", "executive"),
}


def infer_personas(category: str) -> tuple[str, ...]:
    return PERSONAS_BY_CATEGORY.get(category, ("operator",))
