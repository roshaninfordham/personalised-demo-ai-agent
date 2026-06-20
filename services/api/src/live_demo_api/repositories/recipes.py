"""Demo recipe repository."""

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import DemoRecipe, DemoStep
from live_demo_api.db.types import RecipeStatus


class RecipeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_recipe(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        recipe_name: str,
        demo_goal: str,
        target_persona: str | None,
        never_click: list[str],
        global_talk_track: str | None,
        steps: list[dict[str, object]],
        created_by: UUID | None = None,
    ) -> DemoRecipe:
        recipe = DemoRecipe(
            organization_id=organization_id,
            product_id=product_id,
            recipe_name=recipe_name,
            target_persona=target_persona,
            demo_goal=demo_goal,
            never_click=never_click,
            global_talk_track=global_talk_track,
            created_by=created_by,
        )
        self._session.add(recipe)
        await self._session.flush()
        await self.replace_steps(
            organization_id=organization_id, recipe_id=recipe.recipe_id, steps=steps
        )
        await self._session.refresh(recipe)
        return recipe

    async def replace_steps(
        self,
        *,
        organization_id: UUID,
        recipe_id: UUID,
        steps: list[dict[str, object]],
    ) -> None:
        now = datetime.now(UTC)
        await self._session.execute(
            update(DemoStep)
            .where(DemoStep.organization_id == organization_id, DemoStep.recipe_id == recipe_id)
            .values(deleted_at=now)
        )
        for step in steps:
            self._session.add(
                DemoStep(
                    organization_id=organization_id,
                    recipe_id=recipe_id,
                    step_order=cast(int, step["step_order"]),
                    step_key=cast(str, step["step_key"]),
                    goal=cast(str, step["goal"]),
                    screen_hint=cast(str | None, step.get("screen_hint")),
                    click_hint=cast(str | None, step.get("click_hint")),
                    talk_track=cast(str | None, step.get("talk_track")),
                    allowed_actions=cast(list[str], step.get("allowed_actions") or []),
                    success_criteria=cast(list[str], step.get("success_criteria") or []),
                    fallback_strategy=cast(str | None, step.get("fallback_strategy")),
                )
            )
        await self._session.flush()

    async def get_recipe(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        recipe_id: UUID,
    ) -> DemoRecipe | None:
        statement = select(DemoRecipe).where(
            DemoRecipe.organization_id == organization_id,
            DemoRecipe.product_id == product_id,
            DemoRecipe.recipe_id == recipe_id,
            DemoRecipe.deleted_at.is_(None),
        )
        return cast(DemoRecipe | None, await self._session.scalar(statement))

    async def list_recipes(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        limit: int,
        cursor_created_at: datetime | None = None,
        cursor_recipe_id: UUID | None = None,
    ) -> list[DemoRecipe]:
        statement = select(DemoRecipe).where(
            DemoRecipe.organization_id == organization_id,
            DemoRecipe.product_id == product_id,
            DemoRecipe.deleted_at.is_(None),
        )
        if cursor_created_at is not None and cursor_recipe_id is not None:
            statement = statement.where(
                sa.or_(
                    DemoRecipe.created_at < cursor_created_at,
                    sa.and_(
                        DemoRecipe.created_at == cursor_created_at,
                        DemoRecipe.recipe_id < cursor_recipe_id,
                    ),
                )
            )
        statement = statement.order_by(
            DemoRecipe.created_at.desc(), DemoRecipe.recipe_id.desc()
        ).limit(limit)
        return list((await self._session.scalars(statement)).all())

    async def list_steps(self, *, organization_id: UUID, recipe_id: UUID) -> list[DemoStep]:
        statement = (
            select(DemoStep)
            .where(
                DemoStep.organization_id == organization_id,
                DemoStep.recipe_id == recipe_id,
                DemoStep.deleted_at.is_(None),
            )
            .order_by(DemoStep.step_order.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def update_recipe(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        recipe_id: UUID,
        patch: dict[str, object],
    ) -> DemoRecipe | None:
        recipe = await self.get_recipe(
            organization_id=organization_id, product_id=product_id, recipe_id=recipe_id
        )
        if recipe is None:
            return None
        for field in (
            "recipe_name",
            "target_persona",
            "demo_goal",
            "never_click",
            "global_talk_track",
        ):
            if field in patch:
                setattr(recipe, field, patch[field])
        if "steps" in patch:
            await self.replace_steps(
                organization_id=organization_id,
                recipe_id=recipe_id,
                steps=cast(list[dict[str, object]], patch["steps"]),
            )
        await self._session.flush()
        return recipe

    async def activate_recipe(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        recipe_id: UUID,
        target_persona: str | None,
    ) -> DemoRecipe | None:
        persona_filter = (
            DemoRecipe.target_persona.is_(None)
            if target_persona is None
            else DemoRecipe.target_persona == target_persona
        )
        await self._session.execute(
            update(DemoRecipe)
            .where(
                DemoRecipe.organization_id == organization_id,
                DemoRecipe.product_id == product_id,
                persona_filter,
                DemoRecipe.deleted_at.is_(None),
            )
            .values(is_active=False, status=RecipeStatus.DRAFT.value)
        )
        recipe = await self.get_recipe(
            organization_id=organization_id, product_id=product_id, recipe_id=recipe_id
        )
        if recipe is None:
            return None
        recipe.status = RecipeStatus.ACTIVE.value
        recipe.is_active = True
        await self._session.flush()
        return recipe

    async def archive_recipe(
        self, *, organization_id: UUID, product_id: UUID, recipe_id: UUID
    ) -> DemoRecipe | None:
        recipe = await self.get_recipe(
            organization_id=organization_id, product_id=product_id, recipe_id=recipe_id
        )
        if recipe is None:
            return None
        recipe.status = RecipeStatus.ARCHIVED.value
        recipe.is_active = False
        await self._session.flush()
        return recipe

    async def soft_delete_recipe(
        self, *, organization_id: UUID, product_id: UUID, recipe_id: UUID
    ) -> bool:
        recipe = await self.get_recipe(
            organization_id=organization_id, product_id=product_id, recipe_id=recipe_id
        )
        if recipe is None:
            return False
        recipe.deleted_at = datetime.now(UTC)
        recipe.is_active = False
        await self._session.flush()
        return True
