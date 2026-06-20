"""Demo recipe business logic."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.errors import ConflictError, NotFoundError, ValidationAppError
from live_demo_api.events.event_bus import EventBus
from live_demo_api.pagination import clamp_limit, decode_cursor, encode_cursor
from live_demo_api.repositories.products import ProductRepository
from live_demo_api.repositories.recipes import RecipeRepository
from live_demo_api.security import (
    BLOCKED_ALLOWED_ACTION_WORDS,
    STEP_KEY_RE,
    Principal,
    RequestContext,
)
from live_demo_api.services.audit_service import AuditService, publish_event
from live_demo_api.services.mappers import recipe_to_response
from live_demo_contracts.demo_recipe import (
    ActivateDemoRecipeResponse,
    CreateDemoRecipeRequest,
    DemoRecipe,
    DemoStepInput,
    ListDemoRecipesResponse,
    RecipeValidationIssue,
    UpdateDemoRecipeRequest,
    ValidateDemoRecipeResponse,
)


def _cursor_parts(cursor: str | None) -> tuple[datetime | None, UUID | None]:
    if cursor is None:
        return None, None
    decoded = decode_cursor(cursor, max_length=get_settings().max_cursor_length)
    if "created_at" not in decoded or "id" not in decoded:
        return None, None
    return datetime.fromisoformat(decoded["created_at"]), UUID(decoded["id"])


def _text_too_long(value: str | None, maximum: int) -> bool:
    return value is not None and len(value) > maximum


class RecipeService:
    def __init__(self) -> None:
        self._audit = AuditService()

    async def _ensure_product(
        self, db: AsyncSession, principal: Principal, product_id: UUID
    ) -> None:
        product = await ProductRepository(db).get_product(
            organization_id=principal.organization_id,
            product_id=product_id,
        )
        if product is None:
            raise NotFoundError("Product not found.", code="product_not_found")

    def validate_recipe_payload(
        self,
        *,
        recipe_name: str,
        demo_goal: str,
        never_click: list[str],
        steps: list[DemoStepInput],
        global_talk_track: str | None = None,
    ) -> ValidateDemoRecipeResponse:
        settings = get_settings()
        errors: list[RecipeValidationIssue] = []
        warnings: list[RecipeValidationIssue] = []

        if not recipe_name.strip() or len(recipe_name) > 200:
            errors.append(
                RecipeValidationIssue(
                    path="recipe_name",
                    code="invalid_recipe_name",
                    message="Recipe name is required and must be at most 200 characters.",
                )
            )
        if not demo_goal.strip() or len(demo_goal) > settings.recipe_max_text_field_length:
            errors.append(
                RecipeValidationIssue(
                    path="demo_goal",
                    code="invalid_demo_goal",
                    message="Demo goal is required and must fit the configured text limit.",
                )
            )
        if _text_too_long(global_talk_track, settings.recipe_max_text_field_length):
            errors.append(
                RecipeValidationIssue(
                    path="global_talk_track",
                    code="text_too_long",
                    message="Global talk track exceeds the configured text limit.",
                )
            )
        if not steps or len(steps) > settings.recipe_max_steps:
            errors.append(
                RecipeValidationIssue(
                    path="steps",
                    code="invalid_step_count",
                    message=f"Recipe must contain between 1 and {settings.recipe_max_steps} steps.",
                )
            )
        if len(never_click) > settings.recipe_max_never_click_items:
            errors.append(
                RecipeValidationIssue(
                    path="never_click",
                    code="too_many_never_click_items",
                    message="Never-click list exceeds the configured item limit.",
                )
            )
        for index, item in enumerate(never_click):
            if not item.strip() or len(item) > 100:
                errors.append(
                    RecipeValidationIssue(
                        path=f"never_click[{index}]",
                        code="invalid_never_click_item",
                        message=(
                            "Each never-click item must be non-empty and at most 100 characters."
                        ),
                    )
                )

        seen_orders: set[int] = set()
        seen_keys: set[str] = set()
        for index, step in enumerate(steps):
            if step.step_order in seen_orders:
                errors.append(
                    RecipeValidationIssue(
                        path=f"steps[{index}].step_order",
                        code="duplicate_step_order",
                        message="Step order values must be unique.",
                    )
                )
            seen_orders.add(step.step_order)
            if step.step_key in seen_keys:
                errors.append(
                    RecipeValidationIssue(
                        path=f"steps[{index}].step_key",
                        code="duplicate_step_key",
                        message="Step keys must be unique.",
                    )
                )
            seen_keys.add(step.step_key)
            if not STEP_KEY_RE.fullmatch(step.step_key):
                errors.append(
                    RecipeValidationIssue(
                        path=f"steps[{index}].step_key",
                        code="invalid_step_key",
                        message=(
                            "Step key must contain only lowercase letters, numbers, "
                            "hyphen, or underscore."
                        ),
                    )
                )
            if not step.goal.strip():
                errors.append(
                    RecipeValidationIssue(
                        path=f"steps[{index}].goal",
                        code="missing_step_goal",
                        message="Each step must define a goal.",
                    )
                )
            for field in ("goal", "talk_track", "screen_hint", "click_hint", "fallback_strategy"):
                value = getattr(step, field)
                if _text_too_long(value, settings.recipe_max_text_field_length):
                    errors.append(
                        RecipeValidationIssue(
                            path=f"steps[{index}].{field}",
                            code="text_too_long",
                            message="Recipe step text exceeds the configured limit.",
                        )
                    )
            for action_index, action in enumerate(step.allowed_actions):
                lowered = action.lower()
                if any(blocked in lowered for blocked in BLOCKED_ALLOWED_ACTION_WORDS):
                    errors.append(
                        RecipeValidationIssue(
                            path=f"steps[{index}].allowed_actions[{action_index}]",
                            code="blocked_allowed_action",
                            message=(
                                "Allowed actions cannot include destructive or high-risk words."
                            ),
                        )
                    )
        expected_orders = set(range(len(steps)))
        if seen_orders and seen_orders != expected_orders:
            errors.append(
                RecipeValidationIssue(
                    path="steps",
                    code="step_order_not_contiguous",
                    message="Step order must be contiguous from 0.",
                )
            )
        if "Delete" not in never_click:
            warnings.append(
                RecipeValidationIssue(
                    path="never_click",
                    code="default_safety_added",
                    message="Default never-click actions will also be enforced.",
                )
            )
        return ValidateDemoRecipeResponse(valid=not errors, errors=errors, warnings=warnings)

    def _validate_or_raise(
        self,
        *,
        recipe_name: str,
        demo_goal: str,
        never_click: list[str],
        steps: list[DemoStepInput],
        global_talk_track: str | None,
    ) -> None:
        result = self.validate_recipe_payload(
            recipe_name=recipe_name,
            demo_goal=demo_goal,
            never_click=never_click,
            steps=steps,
            global_talk_track=global_talk_track,
        )
        if not result.valid:
            raise ValidationAppError(
                "Recipe validation failed.",
                code="invalid_demo_recipe",
                details={"errors": [issue.model_dump(mode="json") for issue in result.errors]},
            )

    async def create_recipe(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        request: CreateDemoRecipeRequest,
        request_context: RequestContext,
    ) -> DemoRecipe:
        self._validate_or_raise(
            recipe_name=request.recipe_name,
            demo_goal=request.demo_goal,
            never_click=request.never_click,
            steps=request.steps,
            global_talk_track=request.global_talk_track,
        )
        async with db.begin():
            await self._ensure_product(db, principal, product_id)
            recipe = await RecipeRepository(db).create_recipe(
                organization_id=principal.organization_id,
                product_id=product_id,
                recipe_name=request.recipe_name,
                demo_goal=request.demo_goal,
                target_persona=request.target_persona,
                never_click=request.never_click,
                global_talk_track=request.global_talk_track,
                steps=[step.model_dump(mode="json") for step in request.steps],
                created_by=principal.user_id,
            )
            steps = await RecipeRepository(db).list_steps(
                organization_id=principal.organization_id,
                recipe_id=recipe.recipe_id,
            )
            await self._audit.audit(
                db,
                principal=principal,
                action="demo_recipe.create",
                resource_type="demo_recipe",
                resource_id=recipe.recipe_id,
            )
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="demo_recipe.created",
            request_context=request_context,
            payload={"product_id": str(product_id), "recipe_id": str(recipe.recipe_id)},
        )
        return recipe_to_response(recipe, steps)

    async def get_recipe(
        self, db: AsyncSession, principal: Principal, product_id: UUID, recipe_id: UUID
    ) -> DemoRecipe:
        recipe = await RecipeRepository(db).get_recipe(
            organization_id=principal.organization_id,
            product_id=product_id,
            recipe_id=recipe_id,
        )
        if recipe is None:
            raise NotFoundError("Recipe not found.", code="recipe_not_found")
        steps = await RecipeRepository(db).list_steps(
            organization_id=principal.organization_id,
            recipe_id=recipe.recipe_id,
        )
        return recipe_to_response(recipe, steps)

    async def list_recipes(
        self,
        db: AsyncSession,
        principal: Principal,
        product_id: UUID,
        *,
        limit: int | None,
        cursor: str | None,
    ) -> ListDemoRecipesResponse:
        await self._ensure_product(db, principal, product_id)
        settings = get_settings()
        page_limit = clamp_limit(
            limit, default=settings.default_page_limit, maximum=settings.max_page_limit
        )
        cursor_created_at, cursor_recipe_id = _cursor_parts(cursor)
        rows = await RecipeRepository(db).list_recipes(
            organization_id=principal.organization_id,
            product_id=product_id,
            limit=page_limit + 1,
            cursor_created_at=cursor_created_at,
            cursor_recipe_id=cursor_recipe_id,
        )
        next_cursor = None
        if len(rows) > page_limit:
            last = rows[page_limit - 1]
            next_cursor = encode_cursor(
                {"created_at": last.created_at.isoformat(), "id": str(last.recipe_id)}
            )
            rows = rows[:page_limit]
        items: list[DemoRecipe] = []
        repository = RecipeRepository(db)
        for row in rows:
            items.append(
                recipe_to_response(
                    row,
                    await repository.list_steps(
                        organization_id=principal.organization_id,
                        recipe_id=row.recipe_id,
                    ),
                )
            )
        return ListDemoRecipesResponse(items=items, next_cursor=next_cursor)

    async def update_recipe(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        recipe_id: UUID,
        request: UpdateDemoRecipeRequest,
        request_context: RequestContext,
    ) -> DemoRecipe:
        repository = RecipeRepository(db)
        existing = await repository.get_recipe(
            organization_id=principal.organization_id,
            product_id=product_id,
            recipe_id=recipe_id,
        )
        if existing is None:
            raise NotFoundError("Recipe not found.", code="recipe_not_found")
        existing_steps = await repository.list_steps(
            organization_id=principal.organization_id,
            recipe_id=recipe_id,
        )
        current_steps = [
            DemoStepInput(
                step_order=step.step_order,
                step_key=step.step_key,
                goal=step.goal,
                screen_hint=step.screen_hint,
                click_hint=step.click_hint,
                talk_track=step.talk_track,
                allowed_actions=step.allowed_actions,
                success_criteria=step.success_criteria,
                fallback_strategy=step.fallback_strategy,
            )
            for step in existing_steps
        ]
        self._validate_or_raise(
            recipe_name=request.recipe_name
            if request.recipe_name is not None
            else existing.recipe_name,
            demo_goal=request.demo_goal if request.demo_goal is not None else existing.demo_goal,
            never_click=request.never_click
            if request.never_click is not None
            else existing.never_click,
            steps=request.steps if request.steps is not None else current_steps,
            global_talk_track=(
                request.global_talk_track
                if "global_talk_track" in request.model_fields_set
                else existing.global_talk_track
            ),
        )
        patch = request.model_dump(exclude_unset=True, mode="json")
        try:
            updated = await RecipeRepository(db).update_recipe(
                organization_id=principal.organization_id,
                product_id=product_id,
                recipe_id=recipe_id,
                patch=patch,
            )
            if updated is None:
                raise NotFoundError("Recipe not found.", code="recipe_not_found")
            steps = await RecipeRepository(db).list_steps(
                organization_id=principal.organization_id,
                recipe_id=recipe_id,
            )
            await self._audit.audit(
                db,
                principal=principal,
                action="demo_recipe.update",
                resource_type="demo_recipe",
                resource_id=recipe_id,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="demo_recipe.updated",
            request_context=request_context,
            payload={"product_id": str(product_id), "recipe_id": str(recipe_id)},
        )
        return recipe_to_response(updated, steps)

    async def validate_existing_recipe(
        self, db: AsyncSession, principal: Principal, product_id: UUID, recipe_id: UUID
    ) -> ValidateDemoRecipeResponse:
        recipe = await RecipeRepository(db).get_recipe(
            organization_id=principal.organization_id,
            product_id=product_id,
            recipe_id=recipe_id,
        )
        if recipe is None:
            raise NotFoundError("Recipe not found.", code="recipe_not_found")
        steps = await RecipeRepository(db).list_steps(
            organization_id=principal.organization_id,
            recipe_id=recipe_id,
        )
        return self.validate_recipe_payload(
            recipe_name=recipe.recipe_name,
            demo_goal=recipe.demo_goal,
            never_click=recipe.never_click,
            global_talk_track=recipe.global_talk_track,
            steps=[
                DemoStepInput(
                    step_order=step.step_order,
                    step_key=step.step_key,
                    goal=step.goal,
                    screen_hint=step.screen_hint,
                    click_hint=step.click_hint,
                    talk_track=step.talk_track,
                    allowed_actions=step.allowed_actions,
                    success_criteria=step.success_criteria,
                    fallback_strategy=step.fallback_strategy,
                )
                for step in steps
            ],
        )

    async def activate_recipe(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        recipe_id: UUID,
        request_context: RequestContext,
    ) -> ActivateDemoRecipeResponse:
        validation = await self.validate_existing_recipe(db, principal, product_id, recipe_id)
        if not validation.valid:
            raise ValidationAppError(
                "Invalid recipe cannot be activated.",
                code="invalid_demo_recipe",
                details={"errors": [issue.model_dump(mode="json") for issue in validation.errors]},
            )
        try:
            recipe = await RecipeRepository(db).get_recipe(
                organization_id=principal.organization_id,
                product_id=product_id,
                recipe_id=recipe_id,
            )
            if recipe is None:
                raise NotFoundError("Recipe not found.", code="recipe_not_found")
            activated = await RecipeRepository(db).activate_recipe(
                organization_id=principal.organization_id,
                product_id=product_id,
                recipe_id=recipe_id,
                target_persona=recipe.target_persona,
            )
            if activated is None:
                raise ConflictError(
                    "Recipe could not be activated.", code="recipe_activation_failed"
                )
            steps = await RecipeRepository(db).list_steps(
                organization_id=principal.organization_id,
                recipe_id=recipe_id,
            )
            await self._audit.audit(
                db,
                principal=principal,
                action="demo_recipe.activate",
                resource_type="demo_recipe",
                resource_id=recipe_id,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="demo_recipe.activated",
            request_context=request_context,
            payload={"product_id": str(product_id), "recipe_id": str(recipe_id)},
        )
        return ActivateDemoRecipeResponse(recipe=recipe_to_response(activated, steps))

    async def archive_recipe(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        recipe_id: UUID,
        request_context: RequestContext,
    ) -> DemoRecipe:
        async with db.begin():
            recipe = await RecipeRepository(db).archive_recipe(
                organization_id=principal.organization_id,
                product_id=product_id,
                recipe_id=recipe_id,
            )
            if recipe is None:
                raise NotFoundError("Recipe not found.", code="recipe_not_found")
            steps = await RecipeRepository(db).list_steps(
                organization_id=principal.organization_id,
                recipe_id=recipe_id,
            )
            await self._audit.audit(
                db,
                principal=principal,
                action="demo_recipe.archive",
                resource_type="demo_recipe",
                resource_id=recipe_id,
            )
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="demo_recipe.archived",
            request_context=request_context,
            payload={"product_id": str(product_id), "recipe_id": str(recipe_id)},
        )
        return recipe_to_response(recipe, steps)

    async def delete_recipe(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        recipe_id: UUID,
        request_context: RequestContext,
    ) -> None:
        async with db.begin():
            deleted = await RecipeRepository(db).soft_delete_recipe(
                organization_id=principal.organization_id,
                product_id=product_id,
                recipe_id=recipe_id,
            )
            if not deleted:
                raise NotFoundError("Recipe not found.", code="recipe_not_found")
            await self._audit.audit(
                db,
                principal=principal,
                action="demo_recipe.delete",
                resource_type="demo_recipe",
                resource_id=recipe_id,
            )
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="demo_recipe.deleted",
            request_context=request_context,
            payload={"product_id": str(product_id), "recipe_id": str(recipe_id)},
        )
