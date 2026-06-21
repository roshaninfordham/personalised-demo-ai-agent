"""Demo angle generation from deterministic category outputs."""

from __future__ import annotations

ANGLES_BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "analytics_dashboard": ("speed to insight", "metric visibility", "reporting workflow"),
    "crm_sales": ("pipeline visibility", "lead follow-up", "sales execution"),
    "marketing_automation": ("campaign performance", "audience segmentation"),
    "developer_tool": ("implementation speed", "operational visibility"),
    "operations_workflow": ("process consistency", "team execution"),
}


def generate_demo_angles(category: str) -> tuple[str, ...]:
    return ANGLES_BY_CATEGORY.get(category, ("product overview",))
