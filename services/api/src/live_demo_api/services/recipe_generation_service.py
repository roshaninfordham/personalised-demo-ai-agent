"""Recipe generation service facade."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.events.event_bus import EventBus
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.recipe_service import RecipeService
from live_demo_contracts.demo_recipe import GenerateDemoRecipeRequest, GenerateDemoRecipeResponse


class RecipeGenerationService:
    """Narrow facade for text-guidance-to-recipe generation endpoints."""

    def __init__(self, recipe_service: RecipeService | None = None) -> None:
        self._recipe_service = recipe_service or RecipeService()

    async def generate_recipe(
        self,
        db: AsyncSession,
        redis: Redis[Any],
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        request: GenerateDemoRecipeRequest,
        request_context: RequestContext,
    ) -> GenerateDemoRecipeResponse:
        return await self._recipe_service.generate_recipe(
            db,
            redis,
            event_bus,
            principal,
            product_id,
            request,
            request_context,
        )
