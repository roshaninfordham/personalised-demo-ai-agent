from __future__ import annotations

from uuid import UUID

from live_demo_backend_common.recipes.recipe_to_screen_matcher import RecipeToScreenMatcher
from live_demo_backend_common.recipes.recipe_types import (
    CompiledRecipe,
    RecipeStepMatchRequest,
    RecipeStepMatchResult,
    SafeActionContext,
    ScreenContext,
)


class RecipeActionMatcher:
    def __init__(self) -> None:
        self._matcher = RecipeToScreenMatcher()

    async def match(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        session_id: UUID,
        compiled_recipe: CompiledRecipe,
        step_key: str,
        current_screen: ScreenContext,
        safe_actions: tuple[SafeActionContext, ...],
        trace_id: str,
    ) -> RecipeStepMatchResult:
        return await self._matcher.match_step(
            RecipeStepMatchRequest(
                organization_id=organization_id,
                product_id=product_id,
                session_id=session_id,
                compiled_recipe=compiled_recipe,
                step_key=step_key,
                current_screen=current_screen,
                safe_actions=safe_actions,
                trace_id=trace_id,
            )
        )
