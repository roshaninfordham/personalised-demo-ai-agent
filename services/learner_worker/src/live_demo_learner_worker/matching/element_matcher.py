"""Element matching and greedy pair selection."""

from __future__ import annotations

from dataclasses import dataclass

from live_demo_learner_worker.browser.browser_runtime_client import BBox, UIElement
from live_demo_learner_worker.matching.fingerprinting import element_fingerprint
from live_demo_learner_worker.matching.similarity import (
    bbox_similarity,
    jaccard_similarity,
    normalized_levenshtein_similarity,
    token_set,
)


@dataclass(frozen=True, slots=True)
class ElementMatchResult:
    decision: str
    similarity_score: float
    element: UIElement | None


class ElementMatcher:
    def __init__(self, threshold: float = 0.72) -> None:
        self._threshold = threshold

    def score(self, expected: UIElement, observed: UIElement) -> float:
        role_match = 1.0 if expected.role == observed.role else 0.0
        label_similarity = normalized_levenshtein_similarity(expected.label, observed.label)
        surrounding_similarity = jaccard_similarity(
            token_set(expected.surrounding_text), token_set(observed.surrounding_text)
        )
        box_similarity = bbox_similarity(_bbox_map(expected.bbox), _bbox_map(observed.bbox))
        form_context_similarity = 1.0 if expected.action_type == observed.action_type else 0.0
        fingerprint_similarity = (
            1.0 if element_fingerprint(expected) == element_fingerprint(observed) else 0.0
        )
        return round(
            0.25 * role_match
            + 0.25 * label_similarity
            + 0.15 * surrounding_similarity
            + 0.15 * box_similarity
            + 0.10 * form_context_similarity
            + 0.10 * fingerprint_similarity,
            4,
        )

    def best_match(
        self, expected: UIElement, candidates: tuple[UIElement, ...]
    ) -> ElementMatchResult:
        safe_candidates = tuple(
            candidate
            for candidate in candidates
            if candidate.risk_level not in {"high", "blocked"}
            and candidate.action_type == expected.action_type
        )
        if not safe_candidates:
            return ElementMatchResult("not_match", 0.0, None)
        scored = sorted(
            ((self.score(expected, candidate), candidate) for candidate in safe_candidates),
            key=lambda item: (-item[0], item[1].label or "", item[1].element_id),
        )
        score, element = scored[0]
        decision = "matched" if score >= self._threshold else "not_match"
        return ElementMatchResult(decision, score, element if decision == "matched" else None)


def _bbox_map(bbox: BBox | None) -> dict[str, float] | None:
    if bbox is None:
        return None
    return {"x": bbox.x, "y": bbox.y, "width": bbox.width, "height": bbox.height}
