"""Deterministic memory importance scoring."""

from live_demo_agent_runtime.memory.memory_types import MemoryUpdate

BUSINESS_RELEVANCE: dict[str, float] = {
    "objection": 1.0,
    "buying_signal": 1.0,
    "pain_point": 1.0,
    "use_case": 0.8,
    "feature_interest": 0.8,
    "question": 0.7,
    "unanswered_question": 0.7,
    "urgency": 0.7,
    "persona": 0.6,
    "preference": 0.5,
}


def score_memory_importance(
    update: MemoryUpdate,
    *,
    novelty: float = 1.0,
    recency: float = 1.0,
) -> float:
    business_relevance = BUSINESS_RELEVANCE.get(update.type, 0.5)
    specificity = min(1.0, len(update.content) / 120)
    score = (
        0.35 * update.confidence
        + 0.25 * business_relevance
        + 0.20 * max(0.0, min(1.0, novelty))
        + 0.10 * specificity
        + 0.10 * max(0.0, min(1.0, recency))
    )
    return round(max(0.0, min(1.0, score)), 4)
