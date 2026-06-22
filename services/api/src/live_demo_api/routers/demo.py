"""Single-call demo startup API."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
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
from live_demo_api.services.demo_session_service import DemoSessionService
from live_demo_api.services.guidance_service import GuidanceService
from live_demo_api.services.learner_service import LearnerService
from live_demo_api.services.product_service import ProductService
from live_demo_api.services.session_orchestration_service import SessionOrchestrationService
from live_demo_contracts.common import (
    CreateProductGuidanceRequest,
    CreateProductRequest,
    ProductGuidanceType,
)
from live_demo_contracts.demo_session import CreateDemoSessionRequest

router = APIRouter(prefix="/api/v1/demo", tags=["demo-start"])


class StartDemoRequest(BaseModel):
    product_url: str = Field(min_length=1, max_length=2048)
    product_name: str | None = Field(default=None, max_length=300)
    target_persona: str | None = Field(default=None, max_length=300)
    text_guidance: str | None = Field(default=None, max_length=8000)


class StartDemoResponse(BaseModel):
    session_id: str
    status: str
    redirect_url: str


@router.post("/start", response_model=StartDemoResponse, status_code=201)
async def start_demo(
    request: StartDemoRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> StartDemoResponse:
    product_name = request.product_name or _product_name_from_url(request.product_url)
    product = await ProductService().create_product(
        db,
        event_bus,
        principal,
        CreateProductRequest(
            product_name=product_name,
            product_url=request.product_url,
            default_persona=_empty_to_none(request.target_persona),
        ),
        request_context,
    )
    await LearnerService().best_effort_enqueue_product_created(
        db,
        redis,
        principal,
        product_id=UUID(product.product_id),
        product_url=product.product_url,
        request_context=request_context,
    )
    if request.text_guidance and request.text_guidance.strip():
        await GuidanceService().create_guidance(
            db,
            event_bus,
            principal,
            UUID(product.product_id),
            CreateProductGuidanceRequest(
                guidance_type=ProductGuidanceType.TEXT,
                title="Homepage guidance",
                content={"text": request.text_guidance.strip()},
            ),
            request_context,
        )
    session = await DemoSessionService().create_session(
        db,
        redis,
        event_bus,
        principal,
        CreateDemoSessionRequest(
            product_id=product.product_id,
            start_url=product.product_url,
            user_persona=_empty_to_none(request.target_persona),
        ),
        request_context,
    )
    started = await SessionOrchestrationService().start(
        db,
        redis,
        event_bus,
        principal,
        UUID(session.session.session_id),
        request_context,
    )
    return StartDemoResponse(
        session_id=started.session.session_id,
        status=str(started.session.status),
        redirect_url=f"/demo/{started.session.session_id}",
    )


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _product_name_from_url(url: str) -> str:
    without_scheme = url.split("://", 1)[-1]
    host = without_scheme.split("/", 1)[0].removeprefix("www.")
    return host or "Product demo"
