"""Demo recipe API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.dependencies import (
    get_current_principal,
    get_db_session,
    get_event_bus,
    get_request_context,
)
from live_demo_api.events.event_bus import EventBus
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.recipe_service import RecipeService
from live_demo_contracts.demo_recipe import (
    ActivateDemoRecipeResponse,
    CreateDemoRecipeRequest,
    DemoRecipe,
    ListDemoRecipesResponse,
    UpdateDemoRecipeRequest,
    ValidateDemoRecipeResponse,
)

router = APIRouter(prefix="/api/v1/products/{product_id}/recipes", tags=["recipes"])


@router.post("", response_model=DemoRecipe, status_code=status.HTTP_201_CREATED)
async def create_recipe(
    product_id: UUID,
    request: CreateDemoRecipeRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> DemoRecipe:
    return await RecipeService().create_recipe(
        db, event_bus, principal, product_id, request, request_context
    )


@router.get("", response_model=ListDemoRecipesResponse)
async def list_recipes(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> ListDemoRecipesResponse:
    return await RecipeService().list_recipes(db, principal, product_id, limit=limit, cursor=cursor)


@router.get("/{recipe_id}", response_model=DemoRecipe)
async def get_recipe(
    product_id: UUID,
    recipe_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> DemoRecipe:
    return await RecipeService().get_recipe(db, principal, product_id, recipe_id)


@router.patch("/{recipe_id}", response_model=DemoRecipe)
async def update_recipe(
    product_id: UUID,
    recipe_id: UUID,
    request: UpdateDemoRecipeRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> DemoRecipe:
    return await RecipeService().update_recipe(
        db, event_bus, principal, product_id, recipe_id, request, request_context
    )


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(
    product_id: UUID,
    recipe_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> Response:
    await RecipeService().delete_recipe(
        db, event_bus, principal, product_id, recipe_id, request_context
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{recipe_id}/validate", response_model=ValidateDemoRecipeResponse)
async def validate_recipe(
    product_id: UUID,
    recipe_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> ValidateDemoRecipeResponse:
    return await RecipeService().validate_existing_recipe(db, principal, product_id, recipe_id)


@router.post("/{recipe_id}/activate", response_model=ActivateDemoRecipeResponse)
async def activate_recipe(
    product_id: UUID,
    recipe_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> ActivateDemoRecipeResponse:
    return await RecipeService().activate_recipe(
        db, event_bus, principal, product_id, recipe_id, request_context
    )


@router.post("/{recipe_id}/archive", response_model=DemoRecipe)
async def archive_recipe(
    product_id: UUID,
    recipe_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> DemoRecipe:
    return await RecipeService().archive_recipe(
        db, event_bus, principal, product_id, recipe_id, request_context
    )
