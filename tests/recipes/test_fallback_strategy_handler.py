from __future__ import annotations

from uuid import uuid4

import pytest

from live_demo_backend_common.recipes.fallback_strategy_handler import FallbackStrategyHandler
from live_demo_backend_common.recipes.recipe_types import (
    FallbackRequest,
    RecipeProgressState,
    RecipeStepMatchResult,
    RecipeStepStatus,
    SafeActionContext,
    ScreenContext,
)


def _progress(attempts: int = 0) -> RecipeProgressState:
    session_id = uuid4()
    recipe_id = uuid4()
    return RecipeProgressState(
        session_id=session_id,
        recipe_id=recipe_id,
        active_step_key="core_workflow",
        step_statuses={
            "core_workflow": RecipeStepStatus(
                step_key="core_workflow",
                status="in_progress",
                attempt_count=attempts,
            )
        },
        completed_count=0,
        total_count=1,
        progress_ratio=0.0,
        updated_at=RecipeStepStatus("x").updated_at,
    )


def _match() -> RecipeStepMatchResult:
    return RecipeStepMatchResult(
        matched=False,
        step_key="core_workflow",
        screen_id=None,
        screen_match_score=0.1,
        action_id=None,
        action_match_score=0.0,
        confidence=0.1,
        decision="not_found",
        reason_codes=("screen_match_low",),
        evidence={"goal": "add metric"},
    )


@pytest.mark.asyncio
async def test_missing_screen_reads_current_screen() -> None:
    decision = await FallbackStrategyHandler().handle(
        FallbackRequest(
            organization_id=uuid4(),
            product_id=uuid4(),
            session_id=uuid4(),
            recipe_id=uuid4(),
            step_key="core_workflow",
            match_result=_match(),
            current_screen=None,
            safe_actions=(SafeActionContext("read", "read_current_screen", risk_level="low"),),
            progress_state=_progress(),
        )
    )
    assert decision.decision == "read_current_screen"
    assert decision.browser_action_id == "read"


@pytest.mark.asyncio
async def test_blocked_action_never_used_as_fallback() -> None:
    decision = await FallbackStrategyHandler().handle(
        FallbackRequest(
            organization_id=uuid4(),
            product_id=uuid4(),
            session_id=uuid4(),
            recipe_id=uuid4(),
            step_key="core_workflow",
            match_result=_match(),
            current_screen=ScreenContext("screen", "hash", summary="Dashboard"),
            safe_actions=(
                SafeActionContext("delete", "click_element", "Delete", risk_level="blocked"),
            ),
            progress_state=_progress(attempts=3),
            user_utterance=None,
        )
    )
    assert decision.browser_action_id is None
    assert decision.decision in {"enter_recovery", "explain_uncertainty"}
