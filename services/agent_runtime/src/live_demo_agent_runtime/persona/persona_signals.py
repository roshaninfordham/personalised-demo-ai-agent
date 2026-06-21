"""Rule-based persona signal extraction."""

from live_demo_agent_runtime.persona.persona_types import PersonaSignal

ROLES: tuple[str, ...] = (
    "founder",
    "operator",
    "sales",
    "marketing",
    "analytics",
    "engineering",
    "product",
    "customer_success",
    "finance",
    "executive",
    "unknown",
)

ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "founder": ("founder", "ceo", "startup", "fundraising", "runway", "growth"),
    "operator": ("operations", "process", "workflow", "team", "execution"),
    "sales": ("pipeline", "crm", "lead", "quota", "prospect", "deal"),
    "marketing": ("campaign", "attribution", "conversion", "channel"),
    "analytics": ("dashboard", "metrics", "reporting", "kpi", "data"),
    "engineering": ("api", "integration", "security", "deploy", "architecture"),
    "finance": ("revenue", "cost", "margin", "forecast", "budget"),
    "product": ("roadmap", "feature", "user", "release"),
    "customer_success": ("onboarding", "support", "retention", "customer"),
    "executive": ("strategy", "board", "executive", "leadership"),
}

INTEREST_KEYWORDS = (
    "dashboard",
    "metrics",
    "reporting",
    "export",
    "integration",
    "setup",
    "security",
    "collaboration",
    "automation",
    "roi",
)
PAIN_POINT_KEYWORDS = (
    "struggling with",
    "hard to",
    "takes too long",
    "manual",
    "confusing",
    "expensive",
    "slow",
    "can't see",
    "lack of",
)
OBJECTION_KEYWORDS = (
    "too expensive",
    "not sure",
    "concern",
    "security",
    "setup time",
    "migration",
    "integration",
    "accuracy",
    "trust",
)


def extract_role_signal_weights(text: str) -> dict[str, float]:
    normalized = text.lower()
    scores = {role: 0.0 for role in ROLES}
    for role, keywords in ROLE_KEYWORDS.items():
        scores[role] = sum(0.4 for keyword in keywords if keyword in normalized)
    return scores


def extract_persona_signals(
    text: str,
) -> tuple[
    tuple[PersonaSignal, ...],
    tuple[PersonaSignal, ...],
    tuple[PersonaSignal, ...],
]:
    normalized = text.lower()
    interests = tuple(
        PersonaSignal(keyword, 0.7, text) for keyword in INTEREST_KEYWORDS if keyword in normalized
    )
    pain_points = tuple(
        PersonaSignal(keyword, 0.75, text)
        for keyword in PAIN_POINT_KEYWORDS
        if keyword in normalized
    )
    objections = tuple(
        PersonaSignal(keyword, 0.75, text)
        for keyword in OBJECTION_KEYWORDS
        if keyword in normalized
    )
    return interests, pain_points, objections
