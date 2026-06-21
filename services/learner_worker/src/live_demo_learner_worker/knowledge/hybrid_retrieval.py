"""Hybrid retrieval scoring."""

from __future__ import annotations


def hybrid_score(
    vector_score: float | None,
    lexical_score: float | None,
    *,
    vector_weight: float = 0.70,
    lexical_weight: float = 0.30,
) -> float:
    if vector_score is None and lexical_score is None:
        return 0.0
    if vector_score is None:
        return round(max(0.0, min(1.0, lexical_score or 0.0)), 4)
    if lexical_score is None:
        return round(max(0.0, min(1.0, vector_score)), 4)
    return round(
        vector_weight * max(0.0, min(1.0, vector_score))
        + lexical_weight * max(0.0, min(1.0, lexical_score)),
        4,
    )
