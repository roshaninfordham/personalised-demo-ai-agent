"""Demo session API routes."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from live_demo_api.agentic.turn_planner import plan_text_turn
from live_demo_api.clients.browser_runtime_client import BrowserRuntimeClient
from live_demo_api.db.models import ActionEvent, TranscriptEvent
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
from live_demo_api.live_state.live_state_store import LiveStateStore
from live_demo_api.live_state.redis_keys import session_events_stream_key
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.audit_service import publish_event
from live_demo_api.services.demo_session_service import DemoSessionService
from live_demo_api.services.recipe_service import RecipeService
from live_demo_api.services.session_orchestration_service import SessionOrchestrationService
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


class TextTurnRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class TextTurnResponse(BaseModel):
    turn_id: str
    assistant_response: str
    action_taken: str | None = None
    policy_blocked: bool = False
    agent_phase: str | None = None


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
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    request: StartDemoSessionRequest | None = None,
) -> StartDemoSessionResponse:
    _ = request
    return await SessionOrchestrationService().start(
        db, redis, event_bus, principal, session_id, request_context
    )


@router.get("/{session_id}/events")
async def stream_session_events(
    session_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> StreamingResponse:
    await DemoSessionService().get_session(db, principal, session_id)
    stream_key = session_events_stream_key(session_id)
    redis_client = cast(Any, redis)

    async def body() -> AsyncIterator[str]:
        last_id, replay_chunks = await _replay_recent_events(redis_client, stream_key)
        async for chunk in _stream_events(
            request=request,
            redis=redis_client,
            stream_key=stream_key,
            last_id=last_id,
            replay_chunks=replay_chunks,
        ):
            yield chunk

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{session_id}/turns/text", response_model=TextTurnResponse)
async def run_text_turn(
    session_id: UUID,
    request_body: TextTurnRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> TextTurnResponse:
    await DemoSessionService().get_session(db, principal, session_id)
    store = LiveStateStore(cast(Any, redis))
    screen = await store.get_current_screen(session_id) or {}
    safe_actions = await store.get_safe_actions(session_id)
    turn_id = uuid4()
    now = datetime.now(UTC)
    user_text = request_body.text.strip()

    user_event = TranscriptEvent(
        organization_id=principal.organization_id,
        session_id=session_id,
        speaker="user",
        chunk_type="final",
        text=user_text,
        is_final=True,
        confidence=Decimal("1.000"),
        turn_id=turn_id,
    )
    db.add(user_event)
    await db.flush()
    await publish_event(
        event_bus,
        organization_id=principal.organization_id,
        session_id=session_id,
        event_type="transcript.final",
        request_context=request_context,
        payload={
            "transcript_event_id": str(user_event.transcript_event_id),
            "speaker": "user",
            "chunk_type": "final",
            "text": user_text,
            "turn_id": str(turn_id),
        },
    )

    decision = plan_text_turn(user_text, screen, safe_actions).as_router_payload()
    assistant_event = TranscriptEvent(
        organization_id=principal.organization_id,
        session_id=session_id,
        speaker="assistant",
        chunk_type="final",
        text=decision["response"],
        is_final=True,
        confidence=Decimal("0.880"),
        turn_id=turn_id,
    )
    db.add(assistant_event)
    await db.flush()
    await publish_event(
        event_bus,
        organization_id=principal.organization_id,
        session_id=session_id,
        event_type="transcript.final",
        request_context=request_context,
        payload={
            "transcript_event_id": str(assistant_event.transcript_event_id),
            "speaker": "assistant",
            "chunk_type": "final",
            "text": decision["response"],
            "turn_id": str(turn_id),
            "agent_phase": decision["phase"],
            "reason_code": decision["reason_code"],
        },
    )
    await publish_event(
        event_bus,
        organization_id=principal.organization_id,
        session_id=session_id,
        event_type="agent.phase.updated",
        request_context=request_context,
        payload={
            "phase": decision["phase"],
            "turn_id": str(turn_id),
            "reason_code": decision["reason_code"],
        },
    )

    if decision["blocked"]:
        db.add(
            ActionEvent(
                organization_id=principal.organization_id,
                session_id=session_id,
                turn_id=turn_id,
                action_type=str(decision["action_type"] or "blocked_action"),
                action_payload={"label": decision["label"], "source": "text_turn"},
                risk_level="blocked",
                policy_decision="blocked",
                success=False,
                error_code="policy_blocked",
                error_message="Dangerous action blocked by demo policy.",
                latency_ms=0,
            )
        )
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=session_id,
            event_type="browser.action.failed",
            request_context=request_context,
            payload={
                "policy_decision": "blocked",
                "reason_code": "dangerous_action",
                "label": decision["label"],
                "success": False,
            },
        )
    elif decision["action"] is not None:
        browser_executed = await _execute_browser_action_if_possible(
            store=store,
            session_id=session_id,
            action=cast(dict[str, object], decision["action"]),
            request_context=request_context,
        )
        if browser_executed:
            db.add(
                ActionEvent(
                    organization_id=principal.organization_id,
                    session_id=session_id,
                    turn_id=turn_id,
                    action_type=str(decision["action"].get("action_type") or "browser_action"),
                    action_payload={
                        "label": decision["action"].get("label"),
                        "source": "text_turn_browser_runtime",
                    },
                    risk_level=str(decision["action"].get("risk_level") or "low"),
                    policy_decision="allowed",
                    success=True,
                    latency_ms=0,
                )
            )
        else:
            bbox = _action_bbox(cast(dict[str, object], decision["action"]))
            center = _bbox_center(bbox)
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="browser.cursor.move",
                request_context=request_context,
                payload={"x": center[0], "y": center[1], "duration_ms": 320},
            )
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="browser.element.highlight",
                request_context=request_context,
                payload={
                    "element_id": str(decision["action"].get("action_id") or "suggested_action"),
                    "label": str(decision["action"].get("label") or "Suggested action"),
                    "bbox": bbox,
                    "risk_level": str(decision["action"].get("risk_level") or "low"),
                    "duration_ms": 2200,
                },
            )
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="browser.cursor.click",
                request_context=request_context,
                payload={"x": center[0], "y": center[1]},
            )
            db.add(
                ActionEvent(
                    organization_id=principal.organization_id,
                    session_id=session_id,
                    turn_id=turn_id,
                    action_type=str(decision["action"].get("action_type") or "highlight_element"),
                    action_payload={
                        "label": decision["action"].get("label"),
                        "source": "text_turn",
                    },
                    risk_level=str(decision["action"].get("risk_level") or "low"),
                    policy_decision="allowed",
                    success=True,
                    latency_ms=240,
                )
            )
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="browser.action.completed",
                request_context=request_context,
                payload={
                    "action_id": str(decision["action"].get("action_id") or ""),
                    "label": str(decision["action"].get("label") or ""),
                    "success": True,
                    "latency_ms": 240,
                },
            )
    await store.append_transcript_window(
        session_id,
        {
            "speaker": "user",
            "chunk_type": "final",
            "text": user_text,
            "turn_id": str(turn_id),
            "created_at": now.isoformat(),
        },
    )
    await store.append_transcript_window(
        session_id,
        {
            "speaker": "assistant",
            "chunk_type": "final",
            "text": decision["response"],
            "turn_id": str(turn_id),
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    await db.commit()
    return TextTurnResponse(
        turn_id=str(turn_id),
        assistant_response=str(decision["response"]),
        action_taken=str(decision["label"]) if decision["action"] is not None else None,
        policy_blocked=bool(decision["blocked"]),
        agent_phase=str(decision["phase"]),
    )


@router.post("/{session_id}/end", response_model=EndDemoSessionResponse)
async def end_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    request: EndDemoSessionRequest | None = None,
) -> EndDemoSessionResponse:
    return await SessionOrchestrationService().end(
        db, redis, event_bus, principal, session_id, request, request_context
    )


@router.post("/{session_id}/prewarm")
async def prewarm_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> dict[str, object]:
    return await SessionOrchestrationService().prewarm(
        db, redis, event_bus, principal, session_id, request_context
    )


@router.post("/{session_id}/recover")
async def recover_session(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
    body: dict[str, object] | None = None,
) -> dict[str, object]:
    reason_code = str((body or {}).get("reason_code") or "unknown")
    return await SessionOrchestrationService().recover(
        db,
        redis,
        event_bus,
        principal,
        session_id,
        request_context,
        reason_code=reason_code,
    )


@router.get("/{session_id}/orchestration-state")
async def get_orchestration_state(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
    event_bus: Annotated[EventBus, Depends(get_event_bus)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    request_context: Annotated[RequestContext, Depends(get_request_context)],
) -> dict[str, object]:
    return await SessionOrchestrationService().get_state(
        db, redis, event_bus, principal, session_id, request_context
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
    return await SessionOrchestrationService().get_join_config(db, principal, session_id)


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


async def _replay_recent_events(redis: Redis[bytes], stream_key: str) -> tuple[str, list[str]]:
    recent = await redis.xrevrange(stream_key, count=50)  # type: ignore[no-untyped-call]
    if not recent:
        return "$", []
    chunks = [
        _sse_chunk(_decode(message_id), _event_type(fields), _event_json(fields))
        for message_id, fields in reversed(recent)
    ]
    return _decode(recent[0][0]), chunks


async def _stream_events(
    *,
    request: Request,
    redis: Redis[bytes],
    stream_key: str,
    last_id: str,
    replay_chunks: list[str],
) -> AsyncIterator[str]:
    for chunk in replay_chunks:
        yield chunk
    next_heartbeat = time.monotonic() + 10
    while not await request.is_disconnected():
        response = await redis.xread({stream_key: last_id}, count=20, block=1000)  # type: ignore[no-untyped-call]
        for _stream_name, messages in response:
            for message_id, fields in messages:
                last_id = _decode(message_id)
                yield _sse_chunk(last_id, _event_type(fields), _event_json(fields))
        if time.monotonic() >= next_heartbeat:
            yield "event: heartbeat\ndata: {\"ok\":true}\n\n"
            next_heartbeat = time.monotonic() + 10
        await asyncio.sleep(0)


def _sse_chunk(message_id: str, event_type: str, event_json: str) -> str:
    lines = [f"id: {message_id}", f"event: {event_type}"]
    for line in event_json.splitlines() or [""]:
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"


def _field(fields: dict[Any, Any], key: str) -> str:
    raw = fields.get(key) or fields.get(key.encode())
    return _decode(raw)


def _event_json(fields: dict[Any, Any]) -> str:
    return _field(fields, "event_json")


def _event_type(fields: dict[Any, Any]) -> str:
    event_type = _field(fields, "event_type")
    if event_type:
        return event_type
    try:
        parsed = json.loads(_event_json(fields))
    except json.JSONDecodeError:
        return "message"
    value = parsed.get("event_type") if isinstance(parsed, dict) else None
    return str(value or "message")


def _decode(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value or "")


async def _execute_browser_action_if_possible(
    *,
    store: LiveStateStore,
    session_id: UUID,
    action: dict[str, object],
    request_context: RequestContext,
) -> bool:
    action_type = str(action.get("action_type") or "")
    if action_type not in {"click_element", "highlight_element", "read_current_screen"}:
        return False
    if action_type in {"click_element", "highlight_element"} and not str(
        action.get("element_id") or ""
    ):
        return False
    browser_status = await store.get_browser_status(session_id)
    if browser_status is None:
        return False
    browser_session_id = browser_status.get("browser_session_id")
    if not isinstance(browser_session_id, str) or not browser_session_id:
        return False
    result = await BrowserRuntimeClient().execute_action(
        browser_session_id=UUID(browser_session_id),
        action=action,
        trace_id=request_context.trace_id,
    )
    return result.get("success") is True


def _action_bbox(action: dict[str, object]) -> dict[str, float]:
    bbox = action.get("bbox")
    if isinstance(bbox, dict):
        x = _float(bbox.get("x"), 720)
        y = _float(bbox.get("y"), 420)
        width = _float(bbox.get("width"), 180)
        height = _float(bbox.get("height"), 80)
        return {"x": x, "y": y, "width": width, "height": height}
    label = str(action.get("label") or "").lower()
    if "metric" in label:
        return {"x": 550, "y": 462, "width": 340, "height": 176}
    if "report" in label:
        return {"x": 1004, "y": 462, "width": 340, "height": 176}
    return {"x": 96, "y": 462, "width": 340, "height": 176}


def _bbox_center(bbox: dict[str, float]) -> tuple[float, float]:
    return (bbox["x"] + bbox["width"] / 2, bbox["y"] + bbox["height"] / 2)


def _float(value: object, fallback: float) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return fallback
    return fallback
