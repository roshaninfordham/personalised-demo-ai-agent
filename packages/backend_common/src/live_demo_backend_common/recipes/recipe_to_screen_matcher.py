from __future__ import annotations

import math

from live_demo_backend_common.policy.text_matching import normalize_text
from live_demo_backend_common.recipes.recipe_normalizer import normalize_tokens
from live_demo_backend_common.recipes.recipe_types import (
    RecipeStepMatchRequest,
    RecipeStepMatchResult,
    SafeActionContext,
    ScreenContext,
    ScreenNodeContext,
)

RISK_SCORE = {"low": 1.0, "medium": 0.7, "high": 0.0, "blocked": 0.0, "unknown": 0.2}


class RecipeToScreenMatcher:
    def __init__(
        self,
        *,
        screen_threshold: float = 0.72,
        action_threshold: float = 0.70,
        max_candidate_screens: int = 50,
        max_candidate_actions: int = 50,
    ) -> None:
        self._screen_threshold = screen_threshold
        self._action_threshold = action_threshold
        self._max_candidate_screens = max_candidate_screens
        self._max_candidate_actions = max_candidate_actions

    async def match_step(self, request: RecipeStepMatchRequest) -> RecipeStepMatchResult:
        step = request.compiled_recipe.step_by_key.get(request.step_key)
        if step is None:
            return RecipeStepMatchResult(
                matched=False,
                step_key=request.step_key,
                screen_id=None,
                screen_match_score=0.0,
                action_id=None,
                action_match_score=0.0,
                confidence=0.0,
                decision="not_found",
                reason_codes=("unknown_step_key",),
                evidence={},
            )

        screen_score = max(
            [_screen_match_score(step.screen_hint_tokens, request.current_screen)]
            + [
                _candidate_screen_score(step.screen_hint_tokens, candidate)
                for candidate in request.candidate_screens[: self._max_candidate_screens]
            ]
        )
        action, action_score = _best_action_match(
            step.click_hint_tokens,
            step.allowed_tool_names,
            request.safe_actions[: self._max_candidate_actions],
        )
        if action is not None and action.risk_level in {"blocked", "high"}:
            return RecipeStepMatchResult(
                matched=False,
                step_key=step.step_key,
                screen_id=request.current_screen.screen_id,
                screen_match_score=round(screen_score, 4),
                action_id=action.action_id,
                action_match_score=round(action_score, 4),
                confidence=0.0,
                decision="blocked_by_policy",
                reason_codes=("best_match_unsafe",),
                evidence={"action_label": action.label, "risk_level": action.risk_level},
            )
        confidence = 0.55 * screen_score + 0.35 * action_score + 0.10 * step.source_confidence
        if confidence >= 0.80 and screen_score >= self._screen_threshold:
            decision = "matched"
        elif confidence >= 0.60:
            decision = "possible_match"
        else:
            decision = "not_found"
        return RecipeStepMatchResult(
            matched=decision == "matched",
            step_key=step.step_key,
            screen_id=request.current_screen.screen_id,
            screen_match_score=round(screen_score, 4),
            action_id=action.action_id
            if action is not None and action_score >= self._action_threshold
            else None,
            action_match_score=round(action_score, 4),
            confidence=round(confidence, 4),
            decision=decision,  # type: ignore[arg-type]
            reason_codes=_reason_codes(decision, screen_score, action_score),
            evidence={
                "screen_title": request.current_screen.title,
                "screen_hash": request.current_screen.screen_hash,
                "action_label": action.label if action is not None else None,
                "step_source_confidence": step.source_confidence,
            },
        )


def _screen_match_score(hint_tokens: frozenset[str], screen: ScreenContext) -> float:
    current_tokens = normalize_tokens(
        " ".join(
            value or ""
            for value in (screen.title, screen.summary, screen.visible_text, screen.url_path)
        )
    )
    screen_hint_similarity = jaccard(hint_tokens, current_tokens) if hint_tokens else 0.5
    title_similarity = jaccard(hint_tokens, normalize_tokens(screen.title)) if screen.title else 0.0
    visible_text_similarity = (
        jaccard(hint_tokens, normalize_tokens(screen.visible_text)) if screen.visible_text else 0.0
    )
    screen_type_match = (
        1.0 if screen.screen_type and screen.screen_type.lower() in hint_tokens else 0.0
    )
    url_path_similarity = (
        jaccard(hint_tokens, normalize_tokens(screen.url_path)) if screen.url_path else 0.0
    )
    historical_screen_match = screen.confidence
    return clamp(
        0.25 * screen_hint_similarity
        + 0.20 * title_similarity
        + 0.20 * visible_text_similarity
        + 0.15 * screen_type_match
        + 0.10 * url_path_similarity
        + 0.10 * historical_screen_match
    )


def _candidate_screen_score(hint_tokens: frozenset[str], screen: ScreenNodeContext) -> float:
    synthetic = ScreenContext(
        screen_id=screen.screen_id,
        screen_hash="candidate",
        url_path=screen.url_path,
        title=screen.title,
        summary=screen.summary,
        screen_type=screen.screen_type,
        confidence=max(screen.confidence, screen.historical_match),
    )
    return _screen_match_score(hint_tokens, synthetic)


def _best_action_match(
    click_hint_tokens: frozenset[str],
    allowed_tool_names: frozenset[str],
    safe_actions: tuple[SafeActionContext, ...],
) -> tuple[SafeActionContext | None, float]:
    best: tuple[SafeActionContext | None, float] = (None, 0.0)
    for action in safe_actions:
        action_tokens = normalize_tokens(
            " ".join(value or "" for value in (action.label, action.reason, action.action_type))
        )
        click_hint_similarity = (
            jaccard(click_hint_tokens, action_tokens) if click_hint_tokens else 0.35
        )
        action_label_similarity = (
            jaccard(click_hint_tokens, normalize_tokens(action.label)) if action.label else 0.0
        )
        action_type_allowed = (
            1.0 if not allowed_tool_names or action.action_type in allowed_tool_names else 0.0
        )
        risk_allowed = RISK_SCORE.get(action.risk_level, 0.2)
        visibility_score = 1.0 if action.visible and action.enabled else 0.0
        score = clamp(
            0.30 * click_hint_similarity
            + 0.20 * action_label_similarity
            + 0.15 * action_type_allowed
            + 0.15 * risk_allowed
            + 0.10 * visibility_score
            + 0.10 * action.historical_success
        )
        if _action_sort_key(action, score) > _action_sort_key(best[0], best[1]):
            best = (action, score)
    return best


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def cosine(left: dict[str, int], right: dict[str, int]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(count * right.get(token, 0) for token, count in left.items())
    left_norm = math.sqrt(sum(count * count for count in left.values()))
    right_norm = math.sqrt(sum(count * count for count in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _action_sort_key(action: SafeActionContext | None, score: float) -> tuple[float, int, str]:
    risk_rank = {"low": 0, "medium": 1, "unknown": 2, "high": 3, "blocked": 4}
    if action is None:
        return (score, -99, "")
    return (score, -risk_rank.get(action.risk_level, 2), action.action_id)


def _reason_codes(decision: str, screen_score: float, action_score: float) -> tuple[str, ...]:
    reasons: list[str] = []
    if screen_score < 0.72:
        reasons.append("screen_match_low")
    if action_score < 0.70:
        reasons.append("action_match_low")
    reasons.append(f"recipe_match_{normalize_text(decision).replace(' ', '_')}")
    return tuple(reasons)
