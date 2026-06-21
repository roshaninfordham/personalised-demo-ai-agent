"""Bounded product knowledge retrieval decisions."""

from live_demo_agent_runtime.context.context_types import KnowledgeFactContext, ScreenContext

RETRIEVAL_TRIGGERS = (
    "does it",
    "can it",
    "integrate",
    "pricing",
    "security",
    "export",
    "import",
    "support",
    "how do i",
    "what about",
    "is there",
    "compare",
    "data",
    "api",
    "setup",
)

NO_RETRIEVAL_PHRASES = {"continue", "next", "yes", "okay", "ok", "sure"}


def should_retrieve_knowledge(user_utterance: str, screen: ScreenContext | None) -> bool:
    normalized = " ".join(user_utterance.lower().split())
    if normalized in NO_RETRIEVAL_PHRASES:
        return False
    if screen is not None and "show" in normalized and "dashboard" in screen.summary.lower():
        return False
    return any(trigger in normalized for trigger in RETRIEVAL_TRIGGERS)


def rank_knowledge_facts(
    facts: list[KnowledgeFactContext],
    *,
    top_k: int,
    min_score: float,
) -> tuple[KnowledgeFactContext, ...]:
    ranked = sorted(
        (fact for fact in facts if fact.score >= min_score),
        key=lambda item: (-item.score, item.fact_id),
    )
    return tuple(ranked[:top_k])
