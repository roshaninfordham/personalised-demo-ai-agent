from __future__ import annotations

from live_demo_backend_common.recipes.recipe_normalizer import normalize_tokens
from live_demo_backend_common.recipes.recipe_to_screen_matcher import jaccard
from live_demo_backend_common.recipes.recipe_types import (
    FallbackDecision,
    FallbackRequest,
    SafeActionContext,
)


class FallbackStrategyHandler:
    def __init__(self, *, max_attempts: int = 2) -> None:
        self._max_attempts = max_attempts

    async def handle(self, request: FallbackRequest) -> FallbackDecision:
        current_status = request.progress_state.step_statuses.get(request.step_key)
        attempts = current_status.attempt_count if current_status is not None else 0
        if request.current_screen is None:
            return FallbackDecision(
                decision="read_current_screen",
                spoken_guidance="I am going to re-check the current screen so I stay grounded.",
                browser_action_id=_find_action(request.safe_actions, "read_current_screen"),
                reason_codes=("current_screen_missing",),
                confidence=0.9,
                should_update_progress=False,
                new_progress_status=None,
            )
        go_back = _find_action(request.safe_actions, "go_back")
        if request.match_result.decision == "not_found" and go_back is not None and attempts == 0:
            return FallbackDecision(
                decision="go_back",
                spoken_guidance=(
                    "This screen does not look like the step I expected, so I will go back safely."
                ),
                browser_action_id=go_back,
                reason_codes=("unexpected_screen", "go_back_available"),
                confidence=0.72,
                should_update_progress=True,
                new_progress_status="failed",
            )
        alternative, score = _best_safe_alternative(request)
        if alternative is not None and score >= 0.70:
            return FallbackDecision(
                decision="safe_alternative_action",
                spoken_guidance=(
                    "I do not see the exact button from the recipe, but I found "
                    "a safe similar option. I will use that."
                ),
                browser_action_id=alternative.action_id,
                reason_codes=("safe_alternative_found",),
                confidence=round(score, 4),
                should_update_progress=True,
                new_progress_status="adapted",
            )
        if current_status is not None and attempts >= self._max_attempts:
            terminal = (
                "enter_recovery"
                if request.step_key and current_status.status != "skipped"
                else "skip_step"
            )
            return FallbackDecision(
                decision=terminal,  # type: ignore[arg-type]
                spoken_guidance=(
                    "I cannot verify that step from the current screen, so I will "
                    "avoid clicking around and stick to what I can confirm."
                ),
                browser_action_id=None,
                reason_codes=("fallback_attempts_exceeded",),
                confidence=0.65,
                should_update_progress=True,
                new_progress_status="failed" if terminal == "enter_recovery" else "skipped",
            )
        if request.user_utterance:
            return FallbackDecision(
                decision="ask_user",
                spoken_guidance=(
                    "I do not see that step on the current screen. Would you like "
                    "me to continue with the closest safe workflow?"
                ),
                browser_action_id=None,
                reason_codes=("low_confidence", "user_clarification_available"),
                confidence=0.58,
                should_update_progress=False,
                new_progress_status=None,
            )
        return FallbackDecision(
            decision="explain_uncertainty",
            spoken_guidance=(
                "I cannot verify that step from the current screen, so I will "
                "avoid clicking around and stick to what I can confirm."
            ),
            browser_action_id=None,
            reason_codes=("no_safe_fallback",),
            confidence=0.5,
            should_update_progress=True,
            new_progress_status="failed",
        )


def _find_action(actions: tuple[SafeActionContext, ...], action_type: str) -> str | None:
    for action in actions:
        if action.action_type == action_type and action.risk_level in {"low", "medium"}:
            return action.action_id
    return None


def _best_safe_alternative(request: FallbackRequest) -> tuple[SafeActionContext | None, float]:
    goal_tokens = normalize_tokens(
        " ".join(str(value) for value in request.match_result.evidence.values())
    )
    screen_tokens = normalize_tokens(
        request.current_screen.summary if request.current_screen else None
    )
    best: tuple[SafeActionContext | None, float] = (None, 0.0)
    for action in request.safe_actions:
        if action.risk_level not in {"low", "medium"}:
            continue
        action_tokens = normalize_tokens(
            " ".join(value or "" for value in (action.label, action.reason))
        )
        score = (
            0.35 * jaccard(goal_tokens, action_tokens)
            + 0.25 * jaccard(action_tokens, action_tokens)
            + 0.15 * jaccard(screen_tokens, action_tokens)
            + 0.15 * (1.0 if action.risk_level == "low" else 0.7)
            + 0.10 * action.historical_success
        )
        if (score, action.action_id) > (best[1], best[0].action_id if best[0] else ""):
            best = (action, score)
    return best
