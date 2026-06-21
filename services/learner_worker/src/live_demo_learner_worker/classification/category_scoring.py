"""Deterministic category scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass

from live_demo_learner_worker.browser.browser_runtime_client import SafeAction, UIElement
from live_demo_learner_worker.classification.category_taxonomy import (
    CATEGORY_KEYWORDS,
    UNKNOWN_CATEGORY,
)


@dataclass(frozen=True, slots=True)
class CategoryScore:
    category: str
    confidence: float
    matched_keywords: tuple[str, ...]


def score_categories(
    *,
    screen_summary: str,
    visible_text: str | None,
    element_labels: tuple[str, ...],
    product_name: str | None,
    guidance_text: str | None,
    safe_actions: tuple[SafeAction, ...],
    min_confidence: float = 0.50,
) -> CategoryScore:
    text = _normalize(
        " ".join(
            [
                screen_summary,
                visible_text or "",
                " ".join(element_labels),
                product_name or "",
                guidance_text or "",
                " ".join(action.label for action in safe_actions),
            ]
        )
    )
    raw_scores: dict[str, float] = {}
    matches_by_category: dict[str, tuple[str, ...]] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        matched = tuple(keyword for keyword in keywords if keyword in text)
        keyword_score = len(matched) / len(keywords)
        element_score = _field_score(" ".join(element_labels), keywords)
        navigation_score = _field_score(" ".join(action.label for action in safe_actions), keywords)
        product_score = _field_score(product_name or "", keywords)
        guidance_score = _field_score(guidance_text or "", keywords)
        score = (
            0.35 * keyword_score
            + 0.20 * element_score
            + 0.15 * navigation_score
            + 0.15 * product_score
            + 0.15 * guidance_score
        )
        raw_scores[category] = score
        matches_by_category[category] = matched
    total = sum(raw_scores.values())
    top_category = max(raw_scores, key=lambda key: (raw_scores[key], key))
    top_score = raw_scores[top_category]
    confidence = top_score / total if total > 0 else 0.0
    if top_score < min_confidence and confidence < min_confidence:
        return CategoryScore(UNKNOWN_CATEGORY, round(max(top_score, confidence), 3), ())
    return CategoryScore(top_category, round(confidence, 3), matches_by_category[top_category])


def element_labels(elements: tuple[UIElement, ...]) -> tuple[str, ...]:
    return tuple(element.label or element.text or "" for element in elements if element.visible)


def _field_score(text: str, keywords: tuple[str, ...]) -> float:
    normalized = _normalize(text)
    if not normalized:
        return 0.0
    return len([keyword for keyword in keywords if keyword in normalized]) / len(keywords)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()
