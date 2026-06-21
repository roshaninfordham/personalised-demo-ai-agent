"""Product API routes."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.dependencies import (
    get_current_principal,
    get_db_session,
    get_event_bus,
    get_redis_client,
    get_request_context,
)
from live_demo_api.events.event_bus import EventBus
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.learner_service import LearnerService
from live_demo_api.services.product_service import ProductService
from live_demo_contracts.common import (
    CreateProductRequest,
    ListProductsResponse,
    ProductResponse,
    UpdateProductRequest,
)

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: CreateProductRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> ProductResponse:
    response = await ProductService().create_product(
        db, event_bus, principal, request, request_context
    )
    await LearnerService().best_effort_enqueue_product_created(
        db,
        redis,
        principal,
        product_id=UUID(response.product_id),
        product_url=response.product_url,
        request_context=request_context,
    )
    return response


@router.get("", response_model=ListProductsResponse)
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> ListProductsResponse:
    return await ProductService().list_products(db, principal, limit=limit, cursor=cursor)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> ProductResponse:
    return await ProductService().get_product(db, principal, product_id)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    request: UpdateProductRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> ProductResponse:
    return await ProductService().update_product(
        db, event_bus, principal, product_id, request, request_context
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> Response:
    await ProductService().delete_product(db, event_bus, principal, product_id, request_context)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
