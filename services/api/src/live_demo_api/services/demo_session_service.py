"""Demo-session business logic and deterministic state transitions."""

from __future__ import annotations

from datetime import datetime
from typing import cast
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.db.models import DemoSession as DemoSessionRow
from live_demo_api.db.types import DemoPhase, SessionStatus
from live_demo_api.errors import (
    ConflictError,
    NotFoundError,
    StateTransitionError,
    ValidationAppError,
)
from live_demo_api.events.event_bus import EventBus
from live_demo_api.live_state.latency_store import LatencyStore
from live_demo_api.live_state.live_state_store import LiveStateStore
from live_demo_api.live_state.locks import acquire_lock, release_lock
from live_demo_api.live_state.redis_keys import session_lock_key
from live_demo_api.pagination import clamp_limit, decode_cursor, encode_cursor
from live_demo_api.repositories.demo_sessions import DemoSessionRepository, utc_now
from live_demo_api.repositories.products import ProductRepository
from live_demo_api.repositories.recipes import RecipeRepository
from live_demo_api.security import Principal, RequestContext, normalize_product_url
from live_demo_api.services.audit_service import AuditService, publish_event
from live_demo_api.services.join_config_service import JoinConfigService
from live_demo_api.services.mappers import session_to_response
from live_demo_contracts.common import JsonValue
from live_demo_contracts.demo_session import (
    CreateDemoSessionRequest,
    CreateDemoSessionResponse,
    DemoSession,
    DemoSessionStateResponse,
    EndDemoSessionRequest,
    EndDemoSessionResponse,
    JoinConfigResponse,
    ListDemoSessionsResponse,
    SessionLiveState,
    StartDemoSessionResponse,
)

ALLOWED_TRANSITIONS: dict[SessionStatus, frozenset[SessionStatus]] = {
    SessionStatus.CREATED: frozenset(
        {SessionStatus.PREWARMING, SessionStatus.COMPLETED, SessionStatus.FAILED}
    ),
    SessionStatus.PREWARMING: frozenset(
        {
            SessionStatus.WAITING_FOR_USER,
            SessionStatus.LIVE,
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        }
    ),
    SessionStatus.WAITING_FOR_USER: frozenset(
        {SessionStatus.LIVE, SessionStatus.COMPLETED, SessionStatus.FAILED}
    ),
    SessionStatus.LIVE: frozenset(
        {SessionStatus.ENDING, SessionStatus.COMPLETED, SessionStatus.FAILED}
    ),
    SessionStatus.ENDING: frozenset({SessionStatus.COMPLETED, SessionStatus.FAILED}),
    SessionStatus.COMPLETED: frozenset({SessionStatus.COMPLETED}),
    SessionStatus.FAILED: frozenset({SessionStatus.FAILED}),
}


def validate_session_transition(current: SessionStatus, next_: SessionStatus) -> None:
    if next_ not in ALLOWED_TRANSITIONS[current]:
        raise StateTransitionError(
            f"Cannot transition session from {current.value} to {next_.value}.",
            code="invalid_session_transition",
        )


def _uuid(value: str, field: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValidationAppError(f"{field} must be a valid UUID.", code="invalid_uuid") from exc


def _cursor_parts(cursor: str | None) -> tuple[datetime | None, UUID | None]:
    if cursor is None:
        return None, None
    decoded = decode_cursor(cursor, max_length=get_settings().max_cursor_length)
    if "created_at" not in decoded or "id" not in decoded:
        return None, None
    return datetime.fromisoformat(decoded["created_at"]), UUID(decoded["id"])


class DemoSessionService:
    def __init__(self) -> None:
        self._audit = AuditService()
        self._join_config = JoinConfigService()

    async def _ensure_product(
        self, db: AsyncSession, principal: Principal, product_id: UUID
    ) -> str:
        product = await ProductRepository(db).get_product(
            organization_id=principal.organization_id,
            product_id=product_id,
        )
        if product is None:
            raise NotFoundError("Product not found.", code="product_not_found")
        return product.product_url

    async def _ensure_recipe(
        self,
        db: AsyncSession,
        principal: Principal,
        *,
        product_id: UUID,
        recipe_id: UUID | None,
    ) -> None:
        if recipe_id is None:
            return
        recipe = await RecipeRepository(db).get_recipe(
            organization_id=principal.organization_id,
            product_id=product_id,
            recipe_id=recipe_id,
        )
        if recipe is None:
            raise NotFoundError("Recipe not found.", code="recipe_not_found")

    async def create_session(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        request: CreateDemoSessionRequest,
        request_context: RequestContext,
    ) -> CreateDemoSessionResponse:
        settings = get_settings()
        product_id = _uuid(request.product_id, "product_id")
        recipe_id = _uuid(request.recipe_id, "recipe_id") if request.recipe_id is not None else None
        async with db.begin():
            await self._audit.ensure_local_organization(db, principal)
            product_url = await self._ensure_product(db, principal, product_id)
            await self._ensure_recipe(db, principal, product_id=product_id, recipe_id=recipe_id)
            start_url = normalize_product_url(request.start_url or product_url, settings)
            row = await DemoSessionRepository(db).create_session(
                organization_id=principal.organization_id,
                product_id=product_id,
                recipe_id=recipe_id,
                start_url=start_url,
                user_persona=request.user_persona,
                user_company=request.user_company,
                user_display_name=request.user_display_name,
                user_email=request.user_email,
            )
            await self._audit.audit(
                db,
                principal=principal,
                action="demo_session.create",
                resource_type="demo_session",
                resource_id=row.session_id,
            )
        await self._set_session_state(redis, row)
        await publish_event(
            event_bus,
            organization_id=principal.organization_id,
            session_id=row.session_id,
            event_type="session.created",
            request_context=request_context,
            payload={"session_id": str(row.session_id), "product_id": str(product_id)},
        )
        return CreateDemoSessionResponse(session=session_to_response(row))

    async def get_session(
        self, db: AsyncSession, principal: Principal, session_id: UUID
    ) -> DemoSession:
        row = await DemoSessionRepository(db).get_session(
            organization_id=principal.organization_id,
            session_id=session_id,
        )
        if row is None:
            raise NotFoundError("Session not found.", code="session_not_found")
        return session_to_response(row)

    async def list_sessions(
        self,
        db: AsyncSession,
        principal: Principal,
        *,
        product_id: UUID | None,
        status: SessionStatus | None,
        limit: int | None,
        cursor: str | None,
    ) -> ListDemoSessionsResponse:
        settings = get_settings()
        page_limit = clamp_limit(
            limit, default=settings.default_page_limit, maximum=settings.max_page_limit
        )
        cursor_created_at, cursor_session_id = _cursor_parts(cursor)
        rows = await DemoSessionRepository(db).list_sessions(
            organization_id=principal.organization_id,
            product_id=product_id,
            status=status,
            limit=page_limit + 1,
            cursor_created_at=cursor_created_at,
            cursor_session_id=cursor_session_id,
        )
        next_cursor = None
        if len(rows) > page_limit:
            last = rows[page_limit - 1]
            next_cursor = encode_cursor(
                {"created_at": last.created_at.isoformat(), "id": str(last.session_id)}
            )
            rows = rows[:page_limit]
        return ListDemoSessionsResponse(
            items=[session_to_response(row) for row in rows],
            next_cursor=next_cursor,
        )

    async def start_session(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        session_id: UUID,
        request_context: RequestContext,
    ) -> StartDemoSessionResponse:
        owner_id = request_context.request_id
        lock_key = session_lock_key(session_id)
        if not await acquire_lock(redis, lock_key, owner_id, get_settings().redis_lock_ttl_ms):
            raise ConflictError("Session is locked.", code="session_locked")
        event_type: str | None = None
        try:
            async with db.begin():
                row = await DemoSessionRepository(db).get_session(
                    organization_id=principal.organization_id,
                    session_id=session_id,
                )
                if row is None:
                    raise NotFoundError("Session not found.", code="session_not_found")
                current = SessionStatus(row.status)
                if current in {
                    SessionStatus.PREWARMING,
                    SessionStatus.WAITING_FOR_USER,
                    SessionStatus.LIVE,
                }:
                    updated = row
                elif current == SessionStatus.CREATED:
                    validate_session_transition(current, SessionStatus.PREWARMING)
                    updated_row = await DemoSessionRepository(db).set_status(
                        organization_id=principal.organization_id,
                        session_id=session_id,
                        status=SessionStatus.PREWARMING,
                        current_phase=DemoPhase.PREWARMING,
                        started_at=utc_now(),
                    )
                    if updated_row is None:
                        raise NotFoundError("Session not found.", code="session_not_found")
                    updated = updated_row
                    event_type = "session.prewarming.started"
                else:
                    validate_session_transition(current, SessionStatus.PREWARMING)
                    updated = row
                await self._audit.audit(
                    db,
                    principal=principal,
                    action="demo_session.start",
                    resource_type="demo_session",
                    resource_id=session_id,
                )
            await self._set_session_state(redis, updated)
            if event_type is not None:
                await publish_event(
                    event_bus,
                    organization_id=principal.organization_id,
                    session_id=session_id,
                    event_type=event_type,
                    request_context=request_context,
                    payload={"session_id": str(session_id)},
                )
            join_config = await self._join_config.get_join_config(
                organization_id=principal.organization_id,
                session_id=session_id,
            )
            return StartDemoSessionResponse(
                session=session_to_response(updated), join_config=join_config
            )
        finally:
            await release_lock(redis, lock_key, owner_id)

    async def end_session(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        session_id: UUID,
        request: EndDemoSessionRequest,
        request_context: RequestContext,
    ) -> EndDemoSessionResponse:
        owner_id = request_context.request_id
        lock_key = session_lock_key(session_id)
        if not await acquire_lock(redis, lock_key, owner_id, get_settings().redis_lock_ttl_ms):
            raise ConflictError("Session is locked.", code="session_locked")
        try:
            async with db.begin():
                row = await DemoSessionRepository(db).get_session(
                    organization_id=principal.organization_id,
                    session_id=session_id,
                )
                if row is None:
                    raise NotFoundError("Session not found.", code="session_not_found")
                current = SessionStatus(row.status)
                if current == SessionStatus.FAILED and request.force is not True:
                    raise StateTransitionError(
                        "Failed sessions require force=true to end as completed.",
                        code="invalid_session_transition",
                    )
                if current != SessionStatus.COMPLETED:
                    validate_session_transition(
                        current if current != SessionStatus.FAILED else SessionStatus.ENDING,
                        SessionStatus.COMPLETED,
                    )
                    updated = await DemoSessionRepository(db).set_status(
                        organization_id=principal.organization_id,
                        session_id=session_id,
                        status=SessionStatus.COMPLETED,
                        current_phase=DemoPhase.COMPLETED,
                        ended_at=utc_now(),
                    )
                    if updated is None:
                        raise NotFoundError("Session not found.", code="session_not_found")
                else:
                    updated = row
                await self._audit.audit(
                    db,
                    principal=principal,
                    action="demo_session.end",
                    resource_type="demo_session",
                    resource_id=session_id,
                    metadata={"reason": request.reason or ""},
                )
            await self._set_session_state(redis, updated)
            await publish_event(
                event_bus,
                organization_id=principal.organization_id,
                session_id=session_id,
                event_type="session.ended",
                request_context=request_context,
                payload={"session_id": str(session_id)},
            )
            return EndDemoSessionResponse(session=session_to_response(updated))
        finally:
            await release_lock(redis, lock_key, owner_id)

    async def get_session_state(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        principal: Principal,
        session_id: UUID,
    ) -> DemoSessionStateResponse:
        row = await DemoSessionRepository(db).get_session(
            organization_id=principal.organization_id,
            session_id=session_id,
        )
        if row is None:
            raise NotFoundError("Session not found.", code="session_not_found")
        try:
            store = LiveStateStore(redis)
            latency_store = LatencyStore(redis)
            live_state = SessionLiveState(
                available=True,
                current_screen=await store.get_current_screen(session_id),
                safe_actions=await store.get_safe_actions(session_id),
                browser_status=await store.get_browser_status(session_id),
                latency=cast(
                    dict[str, JsonValue],
                    await latency_store.get_latency_state(session_id),
                ),
                live_state_status="available",
            )
        except RedisError:
            live_state = SessionLiveState(
                available=False,
                current_screen=None,
                safe_actions=[],
                browser_status=None,
                latency={},
                live_state_status="unavailable",
            )
        return DemoSessionStateResponse(session=session_to_response(row), live_state=live_state)

    async def get_join_config(
        self,
        db: AsyncSession,
        principal: Principal,
        session_id: UUID,
    ) -> JoinConfigResponse:
        await self.get_session(db, principal, session_id)
        return await self._join_config.get_join_config(
            organization_id=principal.organization_id,
            session_id=session_id,
        )

    async def _set_session_state(self, redis: Redis[bytes], row: DemoSessionRow) -> None:
        data: dict[str, JsonValue] = {
            "session_id": str(row.session_id),
            "organization_id": str(row.organization_id),
            "product_id": str(row.product_id),
            "recipe_id": str(row.recipe_id) if row.recipe_id is not None else None,
            "status": str(row.status),
            "current_phase": str(row.current_phase),
            "user_persona": row.user_persona,
            "updated_at": row.updated_at.isoformat(),
        }
        await LiveStateStore(redis).set_session_state(row.session_id, data)
