"""Demo session API routes."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.types import SessionStatus
from live_demo_api.dependencies import (
    get_current_principal,
    get_db_session,
    get_event_bus,
    get_redis_client,
    get_request_context,
)
from live_demo_api.errors import ValidationAppError
from live_demo_api.events.event_bus import EventBus
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.demo_session_service import DemoSessionService
from live_demo_api.services.recipe_service import RecipeService
from live_demo_api.services.transcript_service import TranscriptService
from live_demo_contracts.browser_action import BrowserActionsResponse
from live_demo_contracts.demo_recipe import RecipeProgressResponse
from live_demo_contracts.demo_session import (
    CreateDemoSessionRequest,
    CreateDemoSessionResponse,
    DemoSession,
    DemoSessionStateResponse,
    EndDemoSessionRequest,
    EndDemoSessionResponse,
    JoinConfigResponse,
    ListDemoSessionsResponse,
    StartDemoSessionRequest,
    StartDemoSessionResponse,
)
from live_demo_contracts.lead_summary import FeaturesShownResponse

router = APIRouter(prefix="/api/v1/demo-sessions", tags=["demo-sessions"])
product_router = APIRouter(
    prefix="/api/v1/products/{product_id}/demo-sessions", tags=["demo-sessions"]
)


def _parse_status(status: str | None) -> SessionStatus | None:
    if status is None:
        return None
    try:
        return SessionStatus(status)
    except ValueError as exc:
        raise ValidationAppError("Invalid session status.", code="invalid_session_status") from exc


@router.post("", response_model=CreateDemoSessionResponse, status_code=201)
async def create_session(
    request: CreateDemoSessionRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> CreateDemoSessionResponse:
    return await DemoSessionService().create_session(
        db, redis, event_bus, principal, request, request_context
    )


@router.get("", response_model=ListDemoSessionsResponse)
async def list_sessions(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    product_id: UUID | None = None,
    status: str | None = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> ListDemoSessionsResponse:
    return await DemoSessionService().list_sessions(
        db,
        principal,
        product_id=product_id,
        status=_parse_status(status),
        limit=limit,
        cursor=cursor,
    )


@router.get("/{session_id}", response_model=DemoSession)
async def get_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> DemoSession:
    return await DemoSessionService().get_session(db, principal, session_id)


@router.post("/{session_id}/start", response_model=StartDemoSessionResponse)
async def start_session(
    session_id: UUID,
    request: StartDemoSessionRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> StartDemoSessionResponse:
    _ = request
    return await DemoSessionService().start_session(
        db, redis, event_bus, principal, session_id, request_context
    )


@router.post("/{session_id}/end", response_model=EndDemoSessionResponse)
async def end_session(
    session_id: UUID,
    request: EndDemoSessionRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> EndDemoSessionResponse:
    return await DemoSessionService().end_session(
        db, redis, event_bus, principal, session_id, request, request_context
    )


@router.get("/{session_id}/state", response_model=DemoSessionStateResponse)
async def get_session_state(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> DemoSessionStateResponse:
    return await DemoSessionService().get_session_state(db, redis, principal, session_id)


@router.get("/{session_id}/join-config", response_model=JoinConfigResponse)
async def get_join_config(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> JoinConfigResponse:
    return await DemoSessionService().get_join_config(db, principal, session_id)


@router.get("/{session_id}/browser-actions", response_model=BrowserActionsResponse)
async def get_browser_actions(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    action_type: str | None = None,
    policy_decision: str | None = None,
    success: bool | None = None,
    include_payload: bool = False,
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> BrowserActionsResponse:
    return await TranscriptService().list_browser_actions(
        db,
        principal,
        session_id,
        action_type=action_type,
        policy_decision=policy_decision,
        success=success,
        include_payload=include_payload,
        limit=limit,
        cursor=cursor,
    )


@router.get("/{session_id}/features-shown", response_model=FeaturesShownResponse)
async def get_features_shown(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> FeaturesShownResponse:
    return await TranscriptService().features_shown(db, principal, session_id)


@router.get("/{session_id}/recipe-progress", response_model=RecipeProgressResponse)
async def get_recipe_progress(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> RecipeProgressResponse:
    return await RecipeService().initialize_or_get_progress(db, redis, principal, session_id)


@router.post("/{session_id}/recipe-progress/{step_key}/skip", response_model=RecipeProgressResponse)
async def skip_recipe_step(
    session_id: UUID,
    step_key: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> RecipeProgressResponse:
    return await RecipeService().update_progress_step(
        db, redis, event_bus, principal, session_id, step_key, "skipped", request_context
    )


@router.post(
    "/{session_id}/recipe-progress/{step_key}/reset", response_model=RecipeProgressResponse
)
async def reset_recipe_step(
    session_id: UUID,
    step_key: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> RecipeProgressResponse:
    return await RecipeService().update_progress_step(
        db, redis, event_bus, principal, session_id, step_key, "in_progress", request_context
    )


@product_router.get("", response_model=ListDemoSessionsResponse)
async def list_sessions_for_product(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    status: str | None = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> ListDemoSessionsResponse:
    return await DemoSessionService().list_sessions(
        db,
        principal,
        product_id=product_id,
        status=_parse_status(status),
        limit=limit,
        cursor=cursor,
    )
