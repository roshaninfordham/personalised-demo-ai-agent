"""Feature confidence scoring."""

from __future__ import annotations


def feature_confidence(
    *,
    screen_evidence: float,
    action_evidence: float,
    recipe_evidence: float,
    transcript_evidence: float,
    repeated_evidence: float,
) -> float:
    return round(
        max(
            0.0,
            min(
                1.0,
                0.35 * screen_evidence
                + 0.25 * action_evidence
                + 0.20 * recipe_evidence
                + 0.10 * transcript_evidence
                + 0.10 * repeated_evidence,
            ),
        ),
        3,
    )
