"""Demo recipe business logic."""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.db.models import (
    CompiledDemoRecipe as CompiledDemoRecipeModel,
)
from live_demo_api.db.models import (
    Product as ProductModel,
)
from live_demo_api.db.models import (
    RecipeStepProgress as RecipeStepProgressModel,
)
from live_demo_api.errors import ConflictError, NotFoundError, ValidationAppError
from live_demo_api.events.event_bus import EventBus
from live_demo_api.live_state.redis_keys import (
    active_recipe_step_key,
    compiled_recipe_key,
    recipe_hash_key,
    recipe_progress_key,
)
from live_demo_api.pagination import clamp_limit, decode_cursor, encode_cursor
from live_demo_api.repositories.compiled_recipes import CompiledRecipeRepository
from live_demo_api.repositories.demo_sessions import DemoSessionRepository
from live_demo_api.repositories.products import ProductRepository
from live_demo_api.repositories.recipe_progress import (
    RecipeGenerationRunRepository,
    RecipeProgressRepository,
)
from live_demo_api.repositories.recipes import RecipeRepository
from live_demo_api.security import (
    Principal,
    RequestContext,
)
from live_demo_api.services.audit_service import AuditService, publish_event
from live_demo_api.services.mappers import recipe_to_response
from live_demo_backend_common.recipes import RecipeCompiler, RecipeValidator
from live_demo_backend_common.recipes.recipe_generation import (
    RecipeGenerationInput,
    TextGuidanceRecipeGenerator,
)
from live_demo_backend_common.recipes.recipe_hash import sha256_canonical
from live_demo_backend_common.recipes.recipe_types import (
    CompileRecipeRequest,
    RecipeEngineLimits,
)
from live_demo_contracts.common import JsonValue
from live_demo_contracts.demo_recipe import (
    ActivateDemoRecipeResponse,
    CompiledDemoRecipeResponse,
    CreateDemoRecipeRequest,
    DemoRecipe,
    DemoStepInput,
    GenerateDemoRecipeRequest,
    GenerateDemoRecipeResponse,
    ListDemoRecipesResponse,
    RecipeProgressResponse,
    RecipeProgressStatus,
    RecipeStepProgressResponse,
    RecipeValidationIssue,
    UpdateDemoRecipeRequest,
    ValidateDemoRecipeRequest,
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


def _limits() -> RecipeEngineLimits:
    settings = get_settings()
    return RecipeEngineLimits(
        max_steps=settings.recipe_max_steps,
        max_never_click_items=settings.recipe_max_never_click_items,
        max_allowed_actions=settings.recipe_max_allowed_actions,
        max_allowed_domains=settings.recipe_max_allowed_domains,
        max_allowed_form_fields=settings.recipe_max_allowed_form_fields,
        max_text_field_chars=settings.recipe_max_text_field_length,
        max_json_bytes=settings.recipe_max_json_bytes,
        max_json_depth=settings.recipe_max_json_depth,
        max_json_keys=settings.recipe_max_json_keys,
        max_compiled_payload_bytes=settings.recipe_compiler_max_compiled_payload_bytes,
        match_max_candidate_screens=settings.recipe_match_max_candidate_screens,
        match_max_candidate_actions=settings.recipe_match_max_candidate_actions,
        screen_match_threshold=settings.recipe_screen_match_threshold,
        action_match_threshold=settings.recipe_action_match_threshold,
        fallback_max_attempts=settings.recipe_fallback_max_attempts,
    )


def _issue_to_contract(issue: Any) -> RecipeValidationIssue:
    return RecipeValidationIssue(
        path=issue.path,
        code=issue.code,
        message=issue.message,
        severity=issue.severity,
    )


def _step_to_raw(step: DemoStepInput) -> dict[str, object]:
    return step.model_dump(mode="json", exclude_none=True)


def _request_to_raw(
    request: CreateDemoRecipeRequest | UpdateDemoRecipeRequest,
) -> dict[str, object]:
    return request.model_dump(mode="json", exclude_none=True)


def _normalized_recipe_to_contract_payload(recipe: Any) -> dict[str, object]:
    return {
        "recipe_name": recipe.recipe_name,
        "target_persona": recipe.target_persona,
        "demo_goal": recipe.demo_goal,
        "never_click": list(recipe.never_click),
        "allowed_domains": list(recipe.allowed_domains),
        "allowed_form_fields": [
            {
                "field_label_pattern": item.field_label_pattern,
                "field_type": item.field_type,
                "max_chars": item.max_chars,
            }
            for item in recipe.allowed_form_fields
        ],
        "confirmation_required_actions": [
            {
                "action_type": item.action_type,
                "label_pattern": item.label_pattern,
                "reason": item.reason,
            }
            for item in recipe.confirmation_required_actions
        ],
        "global_talk_track": recipe.global_talk_track,
        "steps": [
            {
                "step_order": step.step_order,
                "step_key": step.step_key,
                "goal": step.goal,
                "phase": step.phase,
                "screen_hint": step.screen_hint,
                "click_hint": step.click_hint,
                "talk_track": step.talk_track,
                "allowed_actions": list(step.allowed_actions),
                "success_criteria": list(step.success_criteria),
                "fallback_strategy": step.fallback_strategy,
                "max_attempts": step.max_attempts,
                "required": step.required,
                "confidence": step.confidence,
                "source_references": list(step.source_references),
            }
            for step in recipe.steps
        ],
    }


class RecipeService:
    def __init__(self) -> None:
        self._audit = AuditService()

    async def _ensure_product(
        self, db: AsyncSession, principal: Principal, product_id: UUID
    ) -> ProductModel:
        product = await ProductRepository(db).get_product(
            organization_id=principal.organization_id,
            product_id=product_id,
        )
        if product is None:
            raise NotFoundError("Product not found.", code="product_not_found")
        return product

    def validate_recipe_payload(
        self,
        *,
        recipe_name: str,
        demo_goal: str,
        never_click: list[str],
        steps: list[DemoStepInput],
        global_talk_track: str | None = None,
        target_persona: str | None = None,
        product_url: str | None = None,
        allowed_domains: list[str] | None = None,
        allowed_form_fields: Sequence[object] | None = None,
        confirmation_required_actions: Sequence[object] | None = None,
    ) -> ValidateDemoRecipeResponse:
        raw: dict[str, object] = {
            "recipe_name": recipe_name,
            "target_persona": target_persona,
            "demo_goal": demo_goal,
            "never_click": never_click,
            "allowed_domains": allowed_domains or [],
            "allowed_form_fields": [
                item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                for item in (allowed_form_fields or [])
            ],
            "confirmation_required_actions": [
                item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                for item in (confirmation_required_actions or [])
            ],
            "global_talk_track": global_talk_track,
            "steps": [_step_to_raw(step) for step in steps],
        }
        return self.validate_raw_recipe(raw, product_url=product_url)

    def validate_raw_recipe(
        self, raw_recipe: dict[str, object], *, product_url: str | None = None
    ) -> ValidateDemoRecipeResponse:
        validation = RecipeValidator(limits=_limits(), product_url=product_url).validate(raw_recipe)
        normalized = (
            CreateDemoRecipeRequest.model_validate(
                _normalized_recipe_to_contract_payload(validation.normalized_recipe)
            )
            if validation.normalized_recipe is not None
            else None
        )
        return ValidateDemoRecipeResponse(
            valid=validation.valid,
            errors=[_issue_to_contract(issue) for issue in validation.errors],
            warnings=[_issue_to_contract(issue) for issue in validation.warnings],
            normalized_recipe=normalized,
        )

    def _validate_or_raise(
        self,
        *,
        recipe_name: str,
        demo_goal: str,
        never_click: list[str],
        steps: list[DemoStepInput],
        global_talk_track: str | None,
        target_persona: str | None = None,
        product_url: str | None = None,
        allowed_domains: list[str] | None = None,
        allowed_form_fields: Sequence[object] | None = None,
        confirmation_required_actions: Sequence[object] | None = None,
    ) -> ValidateDemoRecipeResponse:
        result = self.validate_recipe_payload(
            recipe_name=recipe_name,
            demo_goal=demo_goal,
            never_click=never_click,
            steps=steps,
            global_talk_track=global_talk_track,
            target_persona=target_persona,
            product_url=product_url,
            allowed_domains=allowed_domains,
            allowed_form_fields=allowed_form_fields,
            confirmation_required_actions=confirmation_required_actions,
        )
        if not result.valid:
            raise ValidationAppError(
                "Recipe validation failed.",
                code="invalid_demo_recipe",
                details={"errors": [issue.model_dump(mode="json") for issue in result.errors]},
            )
        return result

    async def create_recipe(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        principal: Principal,
        product_id: UUID,
        request: CreateDemoRecipeRequest,
        request_context: RequestContext,
    ) -> DemoRecipe:
        async with db.begin():
            product = await self._ensure_product(db, principal, product_id)
            validation = self._validate_or_raise(
                recipe_name=request.recipe_name,
                target_persona=request.target_persona,
                demo_goal=request.demo_goal,
                never_click=request.never_click,
                steps=request.steps,
                global_talk_track=request.global_talk_track,
                product_url=product.product_url,
                allowed_domains=request.allowed_domains,
                allowed_form_fields=request.allowed_form_fields,
                confirmation_required_actions=request.confirmation_required_actions,
            )
            normalized = validation.normalized_recipe or request
            recipe = await RecipeRepository(db).create_recipe(
                organization_id=principal.organization_id,
                product_id=product_id,
                recipe_name=normalized.recipe_name,
                demo_goal=normalized.demo_goal,
                target_persona=normalized.target_persona,
                never_click=normalized.never_click,
                global_talk_track=normalized.global_talk_track,
                steps=[step.model_dump(mode="json") for step in normalized.steps],
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
            await self._compile_recipe_in_transaction(
                db,
                principal=principal,
                product_id=product_id,
                recipe_id=recipe.recipe_id,
                product_url=product.product_url,
                source_request=normalized,
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
        product = await self._ensure_product(db, principal, product_id)
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
        validation = self._validate_or_raise(
            recipe_name=request.recipe_name
            if request.recipe_name is not None
            else existing.recipe_name,
            target_persona=request.target_persona
            if request.target_persona is not None
            else existing.target_persona,
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
            product_url=product.product_url,
            allowed_domains=request.allowed_domains,
            allowed_form_fields=request.allowed_form_fields,
            confirmation_required_actions=request.confirmation_required_actions,
        )
        patch = request.model_dump(exclude_unset=True, mode="json")
        normalized = validation.normalized_recipe
        if normalized is not None:
            patch.update(
                {
                    "recipe_name": normalized.recipe_name,
                    "target_persona": normalized.target_persona,
                    "demo_goal": normalized.demo_goal,
                    "never_click": normalized.never_click,
                    "global_talk_track": normalized.global_talk_track,
                    "steps": [step.model_dump(mode="json") for step in normalized.steps],
                }
            )
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
            await self._compile_recipe_in_transaction(
                db,
                principal=principal,
                product_id=product_id,
                recipe_id=recipe_id,
                product_url=product.product_url,
                source_request=normalized or request,
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
        product = await self._ensure_product(db, principal, product_id)
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
            target_persona=recipe.target_persona,
            product_url=product.product_url,
        )

    async def validate_submitted_recipe(
        self,
        db: AsyncSession,
        principal: Principal,
        product_id: UUID,
        request: ValidateDemoRecipeRequest | dict[str, object],
    ) -> ValidateDemoRecipeResponse:
        product = await self._ensure_product(db, principal, product_id)
        raw = request.recipe if isinstance(request, ValidateDemoRecipeRequest) else request
        if "recipe" in raw and isinstance(raw["recipe"], dict):
            raw = cast(dict[str, object], raw["recipe"])
        return self.validate_raw_recipe(
            cast(dict[str, object], raw), product_url=product.product_url
        )

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
        product = await self._ensure_product(db, principal, product_id)
        input_hash = sha256_canonical(
            {
                "product_id": str(product_id),
                "target_persona": request.target_persona,
                "text_guidance": request.text_guidance,
            }
        )
        try:
            run = await RecipeGenerationRunRepository(db).create_run(
                organization_id=principal.organization_id,
                product_id=product_id,
                input_hash=input_hash,
            )
            generated = TextGuidanceRecipeGenerator(
                validator=RecipeValidator(limits=_limits(), product_url=product.product_url),
                limits=_limits(),
            ).generate_fallback(
                RecipeGenerationInput(
                    organization_id=str(principal.organization_id),
                    product_id=str(product_id),
                    product_name=product.product_name,
                    product_url=product.product_url,
                    text_guidance=request.text_guidance,
                    target_persona=request.target_persona,
                    product_summary=product.product_summary,
                    trace_id=request_context.trace_id,
                )
            )
            validation = self.validate_raw_recipe(generated, product_url=product.product_url)
            output_hash = sha256_canonical(generated)
            recipe_id: UUID | None = None
            if validation.valid and validation.normalized_recipe is not None:
                normalized = validation.normalized_recipe
                recipe = await RecipeRepository(db).create_recipe(
                    organization_id=principal.organization_id,
                    product_id=product_id,
                    recipe_name=normalized.recipe_name,
                    demo_goal=normalized.demo_goal,
                    target_persona=normalized.target_persona,
                    never_click=normalized.never_click,
                    global_talk_track=normalized.global_talk_track,
                    steps=[step.model_dump(mode="json") for step in normalized.steps],
                    created_by=principal.user_id,
                )
                recipe_id = recipe.recipe_id
                compiled_row = await self._compile_recipe_in_transaction(
                    db,
                    principal=principal,
                    product_id=product_id,
                    recipe_id=recipe.recipe_id,
                    product_url=product.product_url,
                    source_request=normalized,
                )
                await self._cache_compiled_recipe(redis, _compiled_payload_with_id(compiled_row))
                await self._audit.audit(
                    db,
                    principal=principal,
                    action="recipe.generate.completed",
                    resource_type="demo_recipe",
                    resource_id=recipe.recipe_id,
                )
                await RecipeGenerationRunRepository(db).finish_run(
                    run,
                    status="completed",
                    output_hash=output_hash,
                    validation_passed=True,
                )
            else:
                await RecipeGenerationRunRepository(db).finish_run(
                    run,
                    status="validation_failed",
                    output_hash=output_hash,
                    validation_passed=False,
                    error_code="generated_recipe_invalid",
                    error_message="Generated recipe failed validation.",
                )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="recipe.generation.completed"
            if validation.valid
            else "recipe.generation.failed",
            request_context=request_context,
            payload={
                "product_id": str(product_id),
                "recipe_id": str(recipe_id) if recipe_id is not None else None,
                "generation_run_id": str(run.generation_run_id),
            },
        )
        return GenerateDemoRecipeResponse(
            recipe=validation.normalized_recipe
            or CreateDemoRecipeRequest.model_validate(generated),
            validation=validation,
            generation_run_id=str(run.generation_run_id),
            recipe_id=str(recipe_id) if recipe_id is not None else None,
            status="draft" if recipe_id is not None else "validation_failed",
        )

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
        product = await self._ensure_product(db, principal, product_id)
        try:
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
            source = CreateDemoRecipeRequest(
                recipe_name=recipe.recipe_name,
                target_persona=recipe.target_persona,
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
            row = await self._compile_recipe_in_transaction(
                db,
                principal=principal,
                product_id=product_id,
                recipe_id=recipe_id,
                product_url=product.product_url,
                source_request=source,
            )
            await self._audit.audit(
                db,
                principal=principal,
                action="recipe.compile",
                resource_type="demo_recipe",
                resource_id=recipe_id,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        await self._cache_compiled_recipe(redis, _compiled_payload_with_id(row))
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=None,
            event_type="recipe.compiled",
            request_context=request_context,
            payload={"product_id": str(product_id), "recipe_id": str(recipe_id)},
        )
        return _compiled_response(row)

    async def get_compiled_recipe(
        self,
        db: AsyncSession,
        redis: Redis[Any],
        principal: Principal,
        product_id: UUID,
        recipe_id: UUID,
    ) -> CompiledDemoRecipeResponse:
        await self._ensure_product(db, principal, product_id)
        cached = await redis.get(compiled_recipe_key(recipe_id))
        if cached:
            payload = cast(dict[str, object], json.loads(cached))
            return CompiledDemoRecipeResponse(
                compiled_recipe_id=str(payload.get("compiled_recipe_id", "")),
                recipe_id=str(recipe_id),
                recipe_hash=str(payload["recipe_hash"]),
                compiled_hash=str(payload["compiled_hash"]),
                compiled_payload=cast(dict[str, JsonValue], payload),
                status="active",
            )
        row = await CompiledRecipeRepository(db).get_active(
            organization_id=principal.organization_id,
            recipe_id=recipe_id,
        )
        if row is None:
            raise NotFoundError("Compiled recipe not found.", code="compiled_recipe_not_found")
        await self._cache_compiled_recipe(redis, _compiled_payload_with_id(row))
        return _compiled_response(row)

    async def initialize_or_get_progress(
        self,
        db: AsyncSession,
        redis: Redis[Any],
        principal: Principal,
        session_id: UUID,
    ) -> RecipeProgressResponse:
        session = await DemoSessionRepository(db).get_session(
            organization_id=principal.organization_id,
            session_id=session_id,
        )
        if session is None:
            raise NotFoundError("Session not found.", code="session_not_found")
        if session.recipe_id is None:
            raise NotFoundError("Session has no recipe.", code="session_recipe_not_found")
        steps = await RecipeRepository(db).list_steps(
            organization_id=principal.organization_id,
            recipe_id=session.recipe_id,
        )
        try:
            rows = await RecipeProgressRepository(db).initialize_steps(
                organization_id=principal.organization_id,
                session_id=session_id,
                recipe_id=session.recipe_id,
                steps=steps,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        response = _progress_response(session_id, session.recipe_id, rows)
        await self._cache_progress(redis, response)
        return response

    async def update_progress_step(
        self,
        db: AsyncSession,
        redis: Redis[Any],
        event_bus: EventBus,
        principal: Principal,
        session_id: UUID,
        step_key: str,
        status: str,
        request_context: RequestContext,
    ) -> RecipeProgressResponse:
        session = await DemoSessionRepository(db).get_session(
            organization_id=principal.organization_id,
            session_id=session_id,
        )
        if session is None or session.recipe_id is None:
            raise NotFoundError(
                "Session recipe progress not found.", code="recipe_progress_not_found"
            )
        try:
            updated = await RecipeProgressRepository(db).update_step(
                organization_id=principal.organization_id,
                session_id=session_id,
                step_key=step_key,
                status=status,
            )
            if updated is None:
                raise NotFoundError("Recipe step progress not found.", code="recipe_step_not_found")
            rows = await RecipeProgressRepository(db).list_progress(
                organization_id=principal.organization_id,
                session_id=session_id,
            )
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        response = _progress_response(session_id, session.recipe_id, rows)
        await self._cache_progress(redis, response)
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=session_id,
            event_type=f"recipe.step.{status}",
            request_context=request_context,
            payload={"recipe_id": str(session.recipe_id), "step_key": step_key},
        )
        return response

    async def _compile_recipe_in_transaction(
        self,
        db: AsyncSession,
        *,
        principal: Principal,
        product_id: UUID,
        recipe_id: UUID,
        product_url: str,
        source_request: CreateDemoRecipeRequest | UpdateDemoRecipeRequest,
    ) -> CompiledDemoRecipeModel:
        raw = _request_to_raw(source_request)
        validation = RecipeValidator(limits=_limits(), product_url=product_url).validate(raw)
        if not validation.valid or validation.normalized_recipe is None:
            raise ValidationAppError(
                "Recipe validation failed.",
                code="invalid_demo_recipe",
                details={
                    "errors": [
                        _issue_to_contract(issue).model_dump(mode="json")
                        for issue in validation.errors
                    ]
                },
            )
        repository = CompiledRecipeRepository(db)
        version = await repository.next_version(
            organization_id=principal.organization_id,
            recipe_id=recipe_id,
        )
        compiled = RecipeCompiler(
            max_payload_bytes=get_settings().recipe_compiler_max_compiled_payload_bytes
        ).compile(
            CompileRecipeRequest(
                organization_id=principal.organization_id,
                product_id=product_id,
                recipe_id=recipe_id,
                normalized_recipe=validation.normalized_recipe,
                product_url=product_url,
                trace_id="",
                version=version,
            )
        )
        return await repository.upsert_compiled_recipe(
            organization_id=principal.organization_id,
            product_id=product_id,
            recipe_id=recipe_id,
            recipe_version=version,
            recipe_hash=compiled.recipe_hash,
            compiled_hash=compiled.compiled_hash,
            compiled_payload=compiled.payload,
        )

    async def _cache_compiled_recipe(
        self, redis: Redis[Any], compiled_payload: dict[str, object]
    ) -> None:
        recipe_id = str(compiled_payload["recipe_id"])
        await redis.set(
            compiled_recipe_key(recipe_id), json.dumps(compiled_payload, sort_keys=True)
        )
        await redis.set(recipe_hash_key(recipe_id), str(compiled_payload["recipe_hash"]))

    async def _cache_progress(self, redis: Redis[Any], response: RecipeProgressResponse) -> None:
        payload = response.model_dump(mode="json")
        await redis.set(
            recipe_progress_key(response.session_id),
            json.dumps(payload, sort_keys=True),
            ex=get_settings().redis_session_ttl_seconds,
        )
        if response.active_step_key is not None:
            await redis.set(
                active_recipe_step_key(response.session_id),
                response.active_step_key,
                ex=get_settings().redis_session_ttl_seconds,
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


def _compiled_response(row: CompiledDemoRecipeModel) -> CompiledDemoRecipeResponse:
    payload = _compiled_payload_with_id(row)
    return CompiledDemoRecipeResponse(
        compiled_recipe_id=str(row.compiled_recipe_id),
        recipe_id=str(row.recipe_id),
        recipe_hash=row.recipe_hash,
        compiled_hash=row.compiled_hash,
        compiled_payload=cast(dict[str, JsonValue], payload),
        status=row.status,
    )


def _compiled_payload_with_id(row: CompiledDemoRecipeModel) -> dict[str, object]:
    payload = dict(row.compiled_payload)
    payload["compiled_recipe_id"] = str(row.compiled_recipe_id)
    return payload


def _progress_response(
    session_id: UUID, recipe_id: UUID, rows: Sequence[RecipeStepProgressModel]
) -> RecipeProgressResponse:
    steps = [
        RecipeStepProgressResponse(
            step_key=row.step_key,
            status=RecipeProgressStatus(row.status),
            attempt_count=row.attempt_count,
            matched_screen_id=str(row.matched_screen_id) if row.matched_screen_id else None,
            matched_action_id=row.matched_action_id,
            matched_confidence=float(row.matched_confidence),
            failure_reason=row.failure_reason,
            evidence=cast(dict[str, JsonValue], row.evidence or {}),
        )
        for row in rows
    ]
    completed = sum(1 for step in steps if step.status == RecipeProgressStatus.COMPLETED)
    total = len(steps)
    active = next(
        (
            step.step_key
            for step in steps
            if step.status
            in {
                RecipeProgressStatus.PENDING,
                RecipeProgressStatus.IN_PROGRESS,
                RecipeProgressStatus.FAILED,
                RecipeProgressStatus.ADAPTED,
            }
        ),
        None,
    )
    return RecipeProgressResponse(
        session_id=str(session_id),
        recipe_id=str(recipe_id),
        active_step_key=active,
        steps=steps,
        completed_count=completed,
        total_count=total,
        progress_ratio=round(completed / total, 4) if total else 0.0,
    )
