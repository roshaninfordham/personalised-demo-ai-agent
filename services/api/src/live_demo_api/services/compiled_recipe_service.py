"""Compiled recipe service facade."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.events.event_bus import EventBus
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.recipe_service import RecipeService
from live_demo_contracts.demo_recipe import CompiledDemoRecipeResponse


class CompiledRecipeService:
    """Narrow facade for compile/load operations used by hot-path consumers."""

    def __init__(self, recipe_service: RecipeService | None = None) -> None:
        self._recipe_service = recipe_service or RecipeService()

    async def compile_recipe(
        self,
        db: AsyncSession,
        redis: Redis[Any],
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        recipe_id: UUID,
        request_context: RequestContext,
    ) -> CompiledDemoRecipeResponse:
        return await self._recipe_service.compile_recipe(
            db,
            redis,
            event_bus,
            principal,
            product_id,
            recipe_id,
            request_context,
        )

    async def get_compiled_recipe(
        self,
        db: AsyncSession,
        redis: Redis[Any],
        principal: Principal,
        product_id: UUID,
        recipe_id: UUID,
    ) -> CompiledDemoRecipeResponse:
        return await self._recipe_service.get_compiled_recipe(
            db,
            redis,
            principal,
            product_id,
            recipe_id,
        )
