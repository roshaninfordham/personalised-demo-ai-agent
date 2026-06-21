from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import CompiledDemoRecipe


class CompiledRecipeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_compiled_recipe(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        recipe_id: UUID,
        recipe_version: int,
        recipe_hash: str,
        compiled_hash: str,
        compiled_payload: dict[str, object],
    ) -> CompiledDemoRecipe:
        existing = await self.get_by_hash(
            organization_id=organization_id,
            recipe_id=recipe_id,
            recipe_hash=recipe_hash,
        )
        if existing is not None:
            existing.status = "active"
            existing.compiled_hash = compiled_hash
            existing.compiled_payload = compiled_payload
            existing.updated_at = datetime.now(UTC)
            await self._session.flush()
            return existing
        await self.mark_stale(organization_id=organization_id, recipe_id=recipe_id)
        row = CompiledDemoRecipe(
            organization_id=organization_id,
            product_id=product_id,
            recipe_id=recipe_id,
            recipe_version=recipe_version,
            recipe_hash=recipe_hash,
            compiled_hash=compiled_hash,
            compiled_payload=compiled_payload,
            status="active",
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def mark_stale(self, *, organization_id: UUID, recipe_id: UUID) -> None:
        await self._session.execute(
            update(CompiledDemoRecipe)
            .where(
                CompiledDemoRecipe.organization_id == organization_id,
                CompiledDemoRecipe.recipe_id == recipe_id,
                CompiledDemoRecipe.status == "active",
            )
            .values(status="stale", updated_at=datetime.now(UTC))
        )

    async def get_active(
        self, *, organization_id: UUID, recipe_id: UUID
    ) -> CompiledDemoRecipe | None:
        statement = (
            select(CompiledDemoRecipe)
            .where(
                CompiledDemoRecipe.organization_id == organization_id,
                CompiledDemoRecipe.recipe_id == recipe_id,
                CompiledDemoRecipe.status == "active",
                CompiledDemoRecipe.deleted_at.is_(None),
            )
            .order_by(CompiledDemoRecipe.recipe_version.desc())
            .limit(1)
        )
        return cast(CompiledDemoRecipe | None, await self._session.scalar(statement))

    async def get_by_hash(
        self, *, organization_id: UUID, recipe_id: UUID, recipe_hash: str
    ) -> CompiledDemoRecipe | None:
        statement = select(CompiledDemoRecipe).where(
            CompiledDemoRecipe.organization_id == organization_id,
            CompiledDemoRecipe.recipe_id == recipe_id,
            CompiledDemoRecipe.recipe_hash == recipe_hash,
            CompiledDemoRecipe.deleted_at.is_(None),
        )
        return cast(CompiledDemoRecipe | None, await self._session.scalar(statement))

    async def next_version(self, *, organization_id: UUID, recipe_id: UUID) -> int:
        statement = select(
            sa.func.coalesce(sa.func.max(CompiledDemoRecipe.recipe_version), 0)
        ).where(
            CompiledDemoRecipe.organization_id == organization_id,
            CompiledDemoRecipe.recipe_id == recipe_id,
        )
        current = await self._session.scalar(statement)
        return int(current or 0) + 1
