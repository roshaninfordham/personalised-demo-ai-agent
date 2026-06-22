"""Deterministic insight scoring."""

from __future__ import annotations

from uuid import UUID

BUSINESS_RELEVANCE = {
    "pain_point": 0.90,
    "objection": 0.95,
    "buying_signal": 0.95,
    "urgency": 0.90,
    "feature_interest": 0.75,
    "unanswered_question": 0.80,
    "role": 0.65,
    "persona": 0.65,
    "question": 0.60,
    "use_case": 0.80,
    "next_step": 0.85,
    "decision_criteria": 0.85,
}


def evidence_strength(
    *,
    transcript_ids: tuple[UUID, ...] = (),
    action_ids: tuple[UUID, ...] = (),
    screen_ids: tuple[UUID, ...] = (),
    recipe_step_ids: tuple[UUID, ...] = (),
) -> float:
    return min(
        1.0,
        (0.5 if transcript_ids else 0.0)
        + (0.3 if action_ids else 0.0)
        + (0.2 if screen_ids or recipe_step_ids else 0.0),
    )


def score_importance(
    *,
    insight_type: str,
    confidence: float,
    specificity: float,
    recency: float,
    evidence_strength_value: float,
) -> float:
    business_relevance = BUSINESS_RELEVANCE.get(insight_type, 0.6)
    return round(
        max(
            0.0,
            min(
                1.0,
                0.35 * confidence
                + 0.25 * business_relevance
                + 0.20 * specificity
                + 0.10 * recency
                + 0.10 * evidence_strength_value,
            ),
        ),
        3,
    )
