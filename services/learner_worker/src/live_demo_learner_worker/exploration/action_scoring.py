"""Candidate action scoring."""

from __future__ import annotations

from live_demo_learner_worker.browser.browser_runtime_client import SafeAction

DEMO_VALUE_WORDS = ("dashboard", "reports", "analytics", "metrics", "create", "overview")
NAVIGATION_WORDS = ("dashboard", "reports", "settings", "back", "next", "overview")
GENERIC_LABELS = {"click", "button", "more", "menu", "settings"}
RISK_SCORE = {"low": 0.1, "medium": 0.5, "high": 0.9, "blocked": 1.0, "unknown": 0.6}


def score_action(action: SafeAction, *, seen_action_ids: set[str] | None = None) -> float:
    label = action.label.lower()
    demo_value = _contains_any(label, DEMO_VALUE_WORDS)
    navigation_value = _contains_any(label, NAVIGATION_WORDS)
    novelty = 0.2 if seen_action_ids and action.action_id in seen_action_ids else 1.0
    label_quality = 0.3 if label in GENERIC_LABELS or len(label) < 3 else 1.0
    visibility = 1.0 if action.element_id else 0.8
    historical_success = max(0.0, min(1.0, action.score or 0.5))
    risk = RISK_SCORE.get(action.risk_level, 0.6)
    latency_cost = 0.1
    score = (
        0.30 * demo_value
        + 0.20 * navigation_value
        + 0.15 * novelty
        + 0.15 * label_quality
        + 0.10 * visibility
        + 0.10 * historical_success
        - 0.40 * risk
        - 0.10 * latency_cost
    )
    return round(max(0.0, min(1.0, score)), 4)


def rank_actions(actions: tuple[SafeAction, ...], *, limit: int) -> tuple[SafeAction, ...]:
    scored = sorted(
        actions,
        key=lambda action: (-score_action(action), action.label.lower(), action.action_id),
    )
    return tuple(scored[:limit])


def _contains_any(text: str, words: tuple[str, ...]) -> float:
    return 1.0 if any(word in text for word in words) else 0.0
