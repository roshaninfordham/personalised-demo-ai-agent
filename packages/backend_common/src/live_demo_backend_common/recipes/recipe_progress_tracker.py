from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from live_demo_backend_common.recipes.recipe_types import (
    InitializeRecipeProgressRequest,
    RecipeProgressState,
    RecipeStepStatus,
    StepProgressUpdateRequest,
)

ALLOWED_PROGRESS_TRANSITIONS = {
    "pending": {"in_progress", "skipped", "blocked"},
    "in_progress": {"completed", "failed", "skipped", "adapted", "blocked"},
    "failed": {"in_progress", "skipped", "adapted", "blocked"},
    "adapted": {"completed", "failed", "skipped", "blocked"},
    "skipped": set(),
    "completed": set(),
    "blocked": set(),
}


class RecipeProgressTracker:
    def initialize_progress(self, request: InitializeRecipeProgressRequest) -> RecipeProgressState:
        statuses = {
            step.step_key: RecipeStepStatus(step_key=step.step_key)
            for step in request.compiled_recipe.steps_by_order
        }
        return _state(request.session_id, request.recipe_id, statuses)

    def update(
        self,
        state: RecipeProgressState,
        request: StepProgressUpdateRequest,
    ) -> RecipeProgressState:
        current = state.step_statuses.get(request.step_key)
        if current is None:
            raise ValueError("Unknown recipe step.")
        if request.status == current.status:
            return state
        allowed = ALLOWED_PROGRESS_TRANSITIONS[current.status]
        if request.status not in allowed:
            raise ValueError(f"Invalid progress transition {current.status} -> {request.status}.")
        now = datetime.now(UTC)
        updated = replace(
            current,
            status=request.status,
            attempt_count=current.attempt_count
            + (1 if request.status in {"in_progress", "failed", "adapted"} else 0),
            matched_screen_id=request.matched_screen_id or current.matched_screen_id,
            matched_action_id=request.matched_action_id or current.matched_action_id,
            matched_confidence=max(current.matched_confidence, request.matched_confidence),
            failure_reason=request.failure_reason,
            evidence={**current.evidence, **request.evidence},
            updated_at=now,
        )
        statuses = {**state.step_statuses, request.step_key: updated}
        active = (
            request.step_key
            if request.status in {"in_progress", "adapted"}
            else _next_pending(statuses)
        )
        return _state(
            state.session_id, state.recipe_id, statuses, active_step_key=active, updated_at=now
        )

    def completion_met(
        self,
        *,
        success_criteria: tuple[str, ...],
        current_screen_text: str | None,
        browser_action_success: bool = False,
        action_id_matches: bool = False,
        assistant_final_exists: bool = False,
        user_confirmed: bool = False,
        screen_match_confidence: float = 0.0,
    ) -> bool:
        text = (current_screen_text or "").lower()
        for criterion in success_criteria:
            lowered = criterion.lower()
            if "visible" in lowered and screen_match_confidence >= 0.72:
                return True
            if "executed" in lowered and browser_action_success and action_id_matches:
                return True
            if "explained" in lowered and assistant_final_exists:
                return True
            if "confirmed" in lowered and user_confirmed:
                return True
            tokens = [token for token in lowered.split() if len(token) > 2]
            if tokens and all(token in text for token in tokens[:4]):
                return True
        return False


def _state(
    session_id: UUID,
    recipe_id: UUID,
    statuses: dict[str, RecipeStepStatus],
    *,
    active_step_key: str | None = None,
    updated_at: datetime | None = None,
) -> RecipeProgressState:
    total = len(statuses)
    completed = sum(1 for item in statuses.values() if item.status == "completed")
    required_keys = set(statuses)
    required_completed = completed
    ratio = (
        (required_completed / len(required_keys))
        if required_keys
        else (completed / total if total else 0.0)
    )
    return RecipeProgressState(
        session_id=session_id,
        recipe_id=recipe_id,
        active_step_key=active_step_key or _next_pending(statuses),
        step_statuses=statuses,
        completed_count=completed,
        total_count=total,
        progress_ratio=round(ratio, 4),
        updated_at=updated_at or datetime.now(UTC),
    )


def _next_pending(statuses: dict[str, RecipeStepStatus]) -> str | None:
    for key, status in statuses.items():
        if status.status in {"pending", "failed", "adapted"}:
            return key
    return None
