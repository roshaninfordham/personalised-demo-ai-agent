"""Screen matching using bounded deterministic features."""

from __future__ import annotations

from dataclasses import dataclass

from live_demo_learner_worker.browser.browser_runtime_client import BrowserScreenRead
from live_demo_learner_worker.matching.similarity import (
    jaccard_similarity,
    normalized_levenshtein_similarity,
    token_set,
)


@dataclass(frozen=True, slots=True)
class ScreenMatchResult:
    decision: str
    similarity_score: float
    match_features: dict[str, float]


class ScreenMatcher:
    def __init__(self, threshold: float = 0.78) -> None:
        self._threshold = threshold

    def match(self, expected: BrowserScreenRead, observed: BrowserScreenRead) -> ScreenMatchResult:
        url_path_similarity = normalized_levenshtein_similarity(
            expected.screen_state.url_path, observed.screen_state.url_path
        )
        title_similarity = normalized_levenshtein_similarity(
            expected.screen_state.title, observed.screen_state.title
        )
        text_jaccard = jaccard_similarity(
            token_set(expected.screen_state.visible_text),
            token_set(observed.screen_state.visible_text),
        )
        heading_jaccard = jaccard_similarity(
            token_set(expected.screen_state.title), token_set(observed.screen_state.title)
        )
        fingerprint_jaccard = jaccard_similarity(
            {element.element_fingerprint or element.element_id for element in expected.ui_elements},
            {element.element_fingerprint or element.element_id for element in observed.ui_elements},
        )
        safe_action_jaccard = jaccard_similarity(
            {action.label.lower() for action in expected.safe_actions},
            {action.label.lower() for action in observed.safe_actions},
        )
        layout_similarity = 1.0 if len(expected.ui_elements) == len(observed.ui_elements) else 0.5
        features = {
            "url_path_similarity": url_path_similarity,
            "title_similarity": title_similarity,
            "visible_text_token_jaccard": text_jaccard,
            "heading_jaccard": heading_jaccard,
            "element_fingerprint_jaccard": fingerprint_jaccard,
            "safe_action_label_jaccard": safe_action_jaccard,
            "layout_signature_similarity": layout_similarity,
        }
        score = round(
            0.20 * url_path_similarity
            + 0.15 * title_similarity
            + 0.20 * text_jaccard
            + 0.15 * heading_jaccard
            + 0.15 * fingerprint_jaccard
            + 0.10 * safe_action_jaccard
            + 0.05 * layout_similarity,
            4,
        )
        decision = "not_match"
        if score >= self._threshold:
            decision = "matched"
        elif score >= self._threshold - 0.10:
            decision = "possible_match"
        return ScreenMatchResult(decision=decision, similarity_score=score, match_features=features)
