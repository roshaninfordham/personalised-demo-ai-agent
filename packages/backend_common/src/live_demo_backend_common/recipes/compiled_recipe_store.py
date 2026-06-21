from __future__ import annotations

from typing import Protocol
from uuid import UUID

from live_demo_backend_common.recipes.recipe_types import CompiledRecipe


class CompiledRecipeStore(Protocol):
    async def put(self, compiled_recipe: CompiledRecipe) -> None: ...

    async def get(self, recipe_id: UUID) -> CompiledRecipe | None: ...

    async def invalidate(self, recipe_id: UUID) -> None: ...
