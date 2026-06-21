from __future__ import annotations

from uuid import uuid4

import pytest

from live_demo_backend_common.recipes.recipe_progress_tracker import RecipeProgressTracker
from live_demo_backend_common.recipes.recipe_types import (
    CompiledRecipe,
    CompiledRecipeSafetyPolicy,
    CompiledRecipeStep,
    InitializeRecipeProgressRequest,
    StepProgressUpdateRequest,
)


def _compiled() -> CompiledRecipe:
    step = CompiledRecipeStep(
        step_id=uuid4(),
        step_order=0,
        step_key="overview",
        phase="OVERVIEW",
        required=True,
        goal="Show dashboard",
        screen_hint_tokens=frozenset({"dashboard"}),
        click_hint_tokens=frozenset(),
        talk_track=None,
        allowed_tool_names=frozenset({"read_current_screen"}),
        success_criteria=("dashboard visible",),
        fallback_strategy="Read screen",
        max_attempts=2,
        source_confidence=1.0,
    )
    return CompiledRecipe(
        recipe_id=uuid4(),
        product_id=uuid4(),
        recipe_hash="r",
        compiled_hash="c",
        version=1,
        steps_by_order=(step,),
        step_by_key={"overview": step},
        safety_policy=CompiledRecipeSafetyPolicy((), (), (), ()),
        allowed_action_index={},
        never_click_matcher_payload={},
        domain_policy=None,  # type: ignore[arg-type]
        success_criteria_by_step={"overview": ("dashboard visible",)},
        fallback_by_step={},
        context_payload={},
        payload={},
    )


def test_progress_transitions_and_ratio() -> None:
    tracker = RecipeProgressTracker()
    compiled = _compiled()
    state = tracker.initialize_progress(
        InitializeRecipeProgressRequest(uuid4(), uuid4(), compiled.recipe_id, compiled)
    )
    state = tracker.update(
        state,
        StepProgressUpdateRequest(
            uuid4(),
            state.session_id,
            state.recipe_id,
            "overview",
            "in_progress",
            "turn1",
            "event1",
        ),
    )
    state = tracker.update(
        state,
        StepProgressUpdateRequest(
            uuid4(),
            state.session_id,
            state.recipe_id,
            "overview",
            "completed",
            "turn1",
            "event2",
        ),
    )
    assert state.completed_count == 1
    assert state.progress_ratio == 1.0


def test_terminal_completed_cannot_change() -> None:
    tracker = RecipeProgressTracker()
    compiled = _compiled()
    state = tracker.initialize_progress(
        InitializeRecipeProgressRequest(uuid4(), uuid4(), compiled.recipe_id, compiled)
    )
    state = tracker.update(
        state,
        StepProgressUpdateRequest(
            uuid4(), state.session_id, state.recipe_id, "overview", "skipped", "t", "e"
        ),
    )
    with pytest.raises(ValueError):
        tracker.update(
            state,
            StepProgressUpdateRequest(
                uuid4(), state.session_id, state.recipe_id, "overview", "completed", "t", "e2"
            ),
        )
