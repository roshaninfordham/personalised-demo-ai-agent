"""API-facing facade for session orchestration."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.events.event_bus import EventBus
from live_demo_api.orchestration.orchestration_state import OrchestrationState
from live_demo_api.orchestration.orchestration_types import (
    PrewarmSessionRequest,
    RecoverSessionRequest,
    ShutdownSessionRequest,
    StartLiveSessionRequest,
)
from live_demo_api.orchestration.session_orchestrator import SessionOrchestrator
from live_demo_api.repositories.demo_sessions import DemoSessionRepository
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.join_config_service import JoinConfigService
from live_demo_api.services.mappers import session_to_response
from live_demo_contracts.demo_session import (
    EndDemoSessionRequest,
    EndDemoSessionResponse,
    JoinConfigResponse,
    StartDemoSessionResponse,
)


class SessionOrchestrationService:
    def _orchestrator(
        self,
        *,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        request_context: RequestContext,
    ) -> SessionOrchestrator:
        return SessionOrchestrator(
            db=db,
            redis=redis,
            event_bus=event_bus,
            principal=principal,
            request_context=request_context,
        )

    async def prewarm(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        session_id: UUID,
        request_context: RequestContext,
    ) -> dict[str, object]:
        result = await self._orchestrator(
            db=db,
            redis=redis,
            event_bus=event_bus,
            principal=principal,
            request_context=request_context,
        ).prewarm_session(
            PrewarmSessionRequest(
                organization_id=principal.organization_id,
                session_id=session_id,
                trace_id=request_context.trace_id or request_context.request_id,
            )
        )
        return {
            "session_id": str(result.session_id),
            "status": result.status,
            "runtime_state": result.runtime_state,
            "readiness": _readiness_payload(result.readiness),
            "resources": _resources_payload(result.resources),
            "join_config": result.join_config,
        }

    async def start(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        session_id: UUID,
        request_context: RequestContext,
    ) -> StartDemoSessionResponse:
        await self._orchestrator(
            db=db,
            redis=redis,
            event_bus=event_bus,
            principal=principal,
            request_context=request_context,
        ).start_live_session(
            StartLiveSessionRequest(
                organization_id=principal.organization_id,
                session_id=session_id,
                trace_id=request_context.trace_id or request_context.request_id,
            )
        )
        session = await DemoSessionRepository(db).get_session(
            organization_id=principal.organization_id, session_id=session_id
        )
        if session is None:
            raise RuntimeError("session_not_found_after_start")
        join_config = await JoinConfigService().get_join_config(
            organization_id=principal.organization_id, session_id=session_id
        )
        return StartDemoSessionResponse(
            session=session_to_response(session),
            join_config=join_config,
        )

    async def get_state(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        session_id: UUID,
        request_context: RequestContext,
    ) -> dict[str, object]:
        state = await self._orchestrator(
            db=db,
            redis=redis,
            event_bus=event_bus,
            principal=principal,
            request_context=request_context,
        ).get_orchestration_state(principal.organization_id, session_id)
        return _state_payload(state)

    async def recover(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        session_id: UUID,
        request_context: RequestContext,
        reason_code: str = "unknown",
    ) -> dict[str, object]:
        result = await self._orchestrator(
            db=db,
            redis=redis,
            event_bus=event_bus,
            principal=principal,
            request_context=request_context,
        ).recover_session(
            RecoverSessionRequest(
                organization_id=principal.organization_id,
                session_id=session_id,
                reason_code=reason_code,
                trace_id=request_context.trace_id or request_context.request_id,
            )
        )
        return {
            "session_id": str(result.session_id),
            "recovered": result.recovered,
            "decision": result.decision,
            "attempt_count": result.attempt_count,
            "reason_code": result.reason_code,
            "safe_message": result.safe_message,
        }

    async def end(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        session_id: UUID,
        request: EndDemoSessionRequest | None,
        request_context: RequestContext,
    ) -> EndDemoSessionResponse:
        end_request = request or EndDemoSessionRequest()
        await self._orchestrator(
            db=db,
            redis=redis,
            event_bus=event_bus,
            principal=principal,
            request_context=request_context,
        ).shutdown_session(
            ShutdownSessionRequest(
                organization_id=principal.organization_id,
                session_id=session_id,
                reason=end_request.reason,
                trace_id=request_context.trace_id or request_context.request_id,
                force=bool(end_request.force),
            )
        )
        session = await DemoSessionRepository(db).get_session(
            organization_id=principal.organization_id, session_id=session_id
        )
        if session is None:
            raise RuntimeError("session_not_found_after_shutdown")
        return EndDemoSessionResponse(session=session_to_response(session))

    async def get_join_config(
        self, db: AsyncSession, principal: Principal, session_id: UUID
    ) -> JoinConfigResponse:
        _ = db
        return await JoinConfigService().get_join_config(
            organization_id=principal.organization_id, session_id=session_id
        )


def _readiness_payload(readiness: object) -> dict[str, object]:
    return {
        "score": cast(Any, readiness).score,
        "browser_ready": cast(Any, readiness).browser_session_ready,
        "first_screen_ready": cast(Any, readiness).first_screen_read,
        "voice_ready": cast(Any, readiness).voice_session_ready,
        "join_config_ready": cast(Any, readiness).join_config_ready,
        "recipe_compiled": cast(Any, readiness).recipe_compiled,
        "learner_enqueued": cast(Any, readiness).learner_enqueued,
        "providers_warmed": cast(Any, readiness).providers_warmed,
        "degraded_reasons": list(cast(Any, readiness).degraded_reasons),
    }


def _resources_payload(resources: object) -> dict[str, object]:
    return {
        resource.resource_type + "_id": resource.resource_id
        for resource in cast(tuple[Any, ...], resources)
        if resource.status in {"allocated", "ready"}
    }


def _state_payload(state: OrchestrationState) -> dict[str, object]:
    return {
        "organization_id": str(state.organization_id),
        "session_id": str(state.session_id),
        "product_id": str(state.product_id),
        "status": state.status,
        "browser_session_id": str(state.browser_session_id) if state.browser_session_id else None,
        "voice_session_id": str(state.voice_session_id) if state.voice_session_id else None,
        "transport_session_id": state.transport_session_id,
        "learner_run_id": str(state.learner_run_id) if state.learner_run_id else None,
        "compiled_recipe_id": str(state.compiled_recipe_id) if state.compiled_recipe_id else None,
        "readiness": _readiness_payload(state.readiness),
        "resources": [
            {
                "resource_type": resource.resource_type,
                "resource_id": resource.resource_id,
                "provider": resource.provider,
                "status": resource.status,
            }
            for resource in state.resources
        ],
        "updated_at": state.updated_at.isoformat(),
    }
