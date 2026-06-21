from __future__ import annotations

from live_demo_learner_worker.knowledge.hybrid_retrieval import hybrid_score


def test_hybrid_score_formula() -> None:
    assert hybrid_score(0.8, 0.6, vector_weight=0.7, lexical_weight=0.3) == 0.74
