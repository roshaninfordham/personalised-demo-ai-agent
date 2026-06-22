"""Helpers for deriving feature labels/categories from evidence."""

from __future__ import annotations

from live_demo_api.post_demo.insights.insight_types import normalize_content

FEATURE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "dashboard": ("dashboard", "overview", "home"),
    "reporting": ("report", "reports", "export", "csv", "download"),
    "analytics": ("analytics", "chart", "graph", "trend", "insight", "metrics"),
    "metric_creation": ("add metric", "create metric", "new metric", "metric builder"),
    "workflow": ("workflow", "task", "process", "automation"),
    "settings": ("settings", "admin", "configuration"),
    "search": ("search", "filter"),
    "integration": ("integration", "api", "webhook"),
}


def classify_feature(text: str) -> tuple[str, str]:
    normalized = normalize_content(text)
    for category, keywords in FEATURE_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            label = category.replace("_", " ").title()
            return category, label
    words = normalized.split()[:3]
    label = " ".join(words).title() if words else "Unknown"
    return "unknown", label
