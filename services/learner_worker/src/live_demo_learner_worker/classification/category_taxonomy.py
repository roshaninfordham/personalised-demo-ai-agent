"""Deterministic product category taxonomy."""

from __future__ import annotations

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "analytics_dashboard": (
        "dashboard",
        "metrics",
        "kpi",
        "report",
        "analytics",
        "chart",
        "revenue",
        "conversion",
    ),
    "crm_sales": (
        "lead",
        "prospect",
        "deal",
        "pipeline",
        "account",
        "opportunity",
        "contact",
        "sales",
    ),
    "marketing_automation": (
        "campaign",
        "audience",
        "attribution",
        "channel",
        "email",
        "conversion",
        "segment",
    ),
    "customer_support": ("ticket", "support", "customer", "sla", "inbox", "conversation"),
    "project_management": ("task", "project", "board", "timeline", "sprint", "milestone"),
    "finance_accounting": ("invoice", "forecast", "budget", "margin", "expense", "revenue"),
    "hr_onboarding": ("employee", "onboarding", "hr", "benefits", "candidate", "payroll"),
    "developer_tool": ("api", "deploy", "logs", "webhook", "sdk", "environment"),
    "security_compliance": ("security", "compliance", "audit", "risk", "policy", "encryption"),
    "data_platform": ("warehouse", "dataset", "pipeline", "schema", "query", "sync"),
    "ecommerce": ("order", "cart", "checkout", "product catalog", "inventory"),
    "content_management": ("content", "publish", "article", "page", "asset", "editor"),
    "education_training": ("course", "lesson", "student", "training", "quiz"),
    "operations_workflow": ("workflow", "process", "operations", "approval", "automation"),
}

UNKNOWN_CATEGORY = "unknown"
