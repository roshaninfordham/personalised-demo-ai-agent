"""Product guidance API routes."""

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
from live_demo_api.services.guidance_service import GuidanceService
from live_demo_contracts.common import (
    CreateProductGuidanceRequest,
    ListProductGuidanceResponse,
    ProductGuidanceResponse,
    UpdateProductGuidanceRequest,
)

router = APIRouter(prefix="/api/v1/products/{product_id}/guidance", tags=["guidance"])


@router.post("", response_model=ProductGuidanceResponse, status_code=status.HTTP_201_CREATED)
async def create_guidance(
    product_id: UUID,
    request: CreateProductGuidanceRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> ProductGuidanceResponse:
    return await GuidanceService().create_guidance(
        db, event_bus, principal, product_id, request, request_context
    )


@router.get("", response_model=ListProductGuidanceResponse)
async def list_guidance(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    guidance_type: str | None = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> ListProductGuidanceResponse:
    return await GuidanceService().list_guidance(
        db,
        principal,
        product_id,
        guidance_type=guidance_type,
        limit=limit,
        cursor=cursor,
    )


@router.get("/{guidance_id}", response_model=ProductGuidanceResponse)
async def get_guidance(
    product_id: UUID,
    guidance_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> ProductGuidanceResponse:
    return await GuidanceService().get_guidance(db, principal, product_id, guidance_id)


@router.patch("/{guidance_id}", response_model=ProductGuidanceResponse)
async def update_guidance(
    product_id: UUID,
    guidance_id: UUID,
    request: UpdateProductGuidanceRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> ProductGuidanceResponse:
    return await GuidanceService().update_guidance(
        db, event_bus, principal, product_id, guidance_id, request, request_context
    )


@router.delete("/{guidance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guidance(
    product_id: UUID,
    guidance_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> Response:
    await GuidanceService().delete_guidance(
        db, event_bus, principal, product_id, guidance_id, request_context
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
