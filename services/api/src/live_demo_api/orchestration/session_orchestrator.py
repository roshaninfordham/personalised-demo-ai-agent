"""State-machine driven end-to-end session orchestrator."""

from __future__ import annotations

import asyncio
from typing import Any, cast
from uuid import UUID, uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.clients.agent_runtime_client import AgentRuntimeClient, VoiceSessionResult
from live_demo_api.clients.browser_runtime_client import (
    BrowserRuntimeClient,
    BrowserScreenResult,
)
from live_demo_api.clients.learner_worker_client import LearnerWorkerClient
from live_demo_api.clients.provider_health_client import ProviderHealthClient
from live_demo_api.config import get_settings
from live_demo_api.db.models import DemoSession as DemoSessionRow
from live_demo_api.db.types import DemoPhase, SessionStatus
from live_demo_api.errors import NotFoundError, StateTransitionError
from live_demo_api.events.event_bus import EventBus
from live_demo_api.live_state.live_state_store import LiveStateStore
from live_demo_api.orchestration.idempotency import IdempotencyStore, derive_idempotency_key
from live_demo_api.orchestration.join_config import sanitize_join_config
from live_demo_api.orchestration.orchestration_events import publish_orchestration_event
from live_demo_api.orchestration.orchestration_locks import SessionOrchestrationLock
from live_demo_api.orchestration.orchestration_metrics import elapsed_ms, perf_counter_ns
from live_demo_api.orchestration.orchestration_recovery import (
    decide_recovery_action,
)
from live_demo_api.orchestration.orchestration_shutdown import (
    deterministic_summary_payload,
    ordered_cleanup_resources,
)
from live_demo_api.orchestration.orchestration_state import (
    OrchestrationState,
    OrchestrationStateStore,
)
from live_demo_api.orchestration.orchestration_types import (
    LiveSessionStartResult,
    PrewarmSessionRequest,
    PrewarmSessionResult,
    ReadinessState,
    RecoverSessionRequest,
    RecoveryResult,
    RecoveryState,
    SessionResource,
    ShutdownSessionRequest,
    ShutdownSessionResult,
    StartLiveSessionRequest,
    utc_now,
)
from live_demo_api.orchestration.readiness import compute_readiness, readiness_allows_start
from live_demo_api.orchestration.resource_cleanup import ResourceCleanup
from live_demo_api.repositories.demo_sessions import DemoSessionRepository
from live_demo_api.repositories.orchestration_runs import OrchestrationRunRepository
from live_demo_api.repositories.products import ProductRepository
from live_demo_api.repositories.session_lifecycle_events import SessionLifecycleEventRepository
from live_demo_api.repositories.session_resource_allocations import (
    SessionResourceAllocationRepository,
)
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.audit_service import AuditService
from live_demo_api.services.join_config_service import JoinConfigService
from live_demo_api.services.recipe_service import RecipeService
from live_demo_backend_common.observability import span_names
from live_demo_backend_common.observability.decorators import trace_async_span


class SessionOrchestrator:
    def __init__(
        self,
        *,
        db: AsyncSession,
        redis: Redis[bytes],
        event_bus: EventBus,
        principal: Principal,
        request_context: RequestContext,
        browser_client: BrowserRuntimeClient | None = None,
        agent_client: AgentRuntimeClient | None = None,
        learner_client: LearnerWorkerClient | None = None,
        provider_health_client: ProviderHealthClient | None = None,
    ) -> None:
        self._db = db
        self._redis = redis
        self._event_bus = event_bus
        self._principal = principal
        self._request_context = request_context
        self._browser = browser_client or BrowserRuntimeClient()
        self._agent = agent_client or AgentRuntimeClient()
        self._learner = learner_client or LearnerWorkerClient()
        self._providers = provider_health_client or ProviderHealthClient()
        self._audit = AuditService()
        self._join_config = JoinConfigService()

    @trace_async_span(span_names.SESSION_PREWARM)
    async def prewarm_session(self, request: PrewarmSessionRequest) -> PrewarmSessionResult:
        key = request.idempotency_key or derive_idempotency_key(
            "prewarm", request.session_id, "waiting_for_user"
        )
        idempotency = IdempotencyStore(self._redis)
        cached = await idempotency.get(request.session_id, "prewarm", key)
        if cached is not None:
            state = await self.get_orchestration_state(request.organization_id, request.session_id)
            return PrewarmSessionResult(
                session_id=request.session_id,
                status=state.status,
                runtime_state=cast(Any, cached.get("runtime_state", "ready")),
                readiness=state.readiness,
                resources=state.resources,
                join_config=cast(dict[str, object] | None, cached.get("join_config")),
            )

        owner_id = str(uuid4())
        async with SessionOrchestrationLock(self._redis, request.session_id, owner_id):
            start_ns = perf_counter_ns()
            session = await self._load_session(request.organization_id, request.session_id)
            product = await ProductRepository(self._db).get_product(
                organization_id=request.organization_id,
                product_id=session.product_id,
            )
            if product is None:
                raise NotFoundError("Product not found.", code="product_not_found")
            current = SessionStatus(session.status)
            if current == SessionStatus.CREATED:
                session = await self._set_session_status(
                    session,
                    status=SessionStatus.PREWARMING,
                    phase=DemoPhase.PREWARMING,
                    trace_id=request.trace_id,
                    event_type="session.prewarming.started",
                )
            elif current in {SessionStatus.WAITING_FOR_USER, SessionStatus.LIVE}:
                state = await self.get_orchestration_state(
                    request.organization_id, request.session_id
                )
                return PrewarmSessionResult(
                    session_id=request.session_id,
                    status=session.status,
                    runtime_state="ready",
                    readiness=state.readiness,
                    resources=state.resources,
                    join_config=None,
                )

            run = await OrchestrationRunRepository(self._db).create_run(
                organization_id=request.organization_id,
                session_id=request.session_id,
                run_type="prewarm",
                trace_id=request.trace_id,
            )
            await self._audit.audit(
                self._db,
                principal=self._principal,
                action="session.prewarm.requested",
                resource_type="demo_session",
                resource_id=request.session_id,
            )
            await self._db.commit()

            browser_task = self._prewarm_browser(session, request.trace_id)
            voice_task = self._prewarm_voice(
                request.organization_id,
                session.product_id,
                request.session_id,
                request.trace_id,
            )
            provider_task = self._providers.warm_all(trace_id=request.trace_id)
            learner_task = self._learner.enqueue_learning_run(
                organization_id=request.organization_id,
                product_id=session.product_id,
                session_id=request.session_id,
                start_url=session.start_url,
                trace_id=request.trace_id,
            )
            results = await asyncio.gather(
                browser_task,
                voice_task,
                provider_task,
                learner_task,
                return_exceptions=True,
            )
            browser_result = results[0] if isinstance(results[0], BrowserScreenResult) else None
            voice_result = results[1] if isinstance(results[1], VoiceSessionResult) else None
            provider_warmed_count = results[2][0] if isinstance(results[2], tuple) else 0
            provider_reasons = (
                results[2][1] if isinstance(results[2], tuple) else ("provider_failed",)
            )
            learner_run_id = results[3] if isinstance(results[3], UUID) else None
            compiled_recipe_id = await self._compile_recipe_if_needed(session, request.trace_id)

            resources = await self._persist_prewarm_resources(
                session=session,
                browser_result=browser_result,
                voice_result=voice_result,
                learner_run_id=learner_run_id,
                compiled_recipe_id=compiled_recipe_id,
            )
            readiness = compute_readiness(
                browser_session_ready=browser_result is not None,
                url_loaded=browser_result is not None,
                first_screen_read=browser_result is not None,
                safe_action_count=len(browser_result.safe_actions) if browser_result else 0,
                voice_session_ready=voice_result is not None,
                join_config_ready=voice_result is not None,
                recipe_compiled=compiled_recipe_id is not None or session.recipe_id is None,
                learner_enqueued=learner_run_id is not None,
                provider_warmed_count=int(provider_warmed_count),
                provider_required_count=3,
                degraded_reasons=tuple(provider_reasons),
            )
            allows_start, runtime_state = readiness_allows_start(readiness)
            if not allows_start:
                session = await self._set_session_status(
                    session,
                    status=SessionStatus.FAILED,
                    phase=DemoPhase.FAILED,
                    trace_id=request.trace_id,
                    event_type="session.prewarming.failed",
                )
                run_status = "failed"
            else:
                session = await self._set_session_status(
                    session,
                    status=SessionStatus.WAITING_FOR_USER,
                    phase=DemoPhase.OVERVIEW,
                    trace_id=request.trace_id,
                    event_type=(
                        "session.prewarming.degraded"
                        if runtime_state == "degraded_ready"
                        else "session.prewarming.completed"
                    ),
                )
                await self._publish(
                    "session.readiness.updated",
                    request.session_id,
                    request.trace_id,
                    {
                        "score": readiness.score,
                        "runtime_state": runtime_state,
                    },
                )
                await self._publish(
                    "session.waiting_for_user",
                    request.session_id,
                    request.trace_id,
                    {"status": "waiting_for_user"},
                )
                run_status = (
                    "completed"
                    if runtime_state != "degraded_ready"
                    else "completed_with_warnings"
                )
            await OrchestrationRunRepository(self._db).finish_run(
                run,
                status=run_status,
                metrics={"duration_ms": elapsed_ms(start_ns), "readiness_score": readiness.score},
            )
            await self._db.commit()
            join_config = sanitize_join_config(voice_result.join_config) if voice_result else None
            await self._write_state(
                session=session,
                readiness=readiness,
                resources=resources,
                browser_session_id=browser_result.browser_session_id if browser_result else None,
                voice_session_id=voice_result.voice_session_id if voice_result else None,
                transport_session_id=voice_result.transport_session_id if voice_result else None,
                learner_run_id=learner_run_id,
                compiled_recipe_id=compiled_recipe_id,
                runtime_state=runtime_state,
            )
            result = PrewarmSessionResult(
                session_id=request.session_id,
                status=session.status,
                runtime_state=cast(Any, runtime_state),
                readiness=readiness,
                resources=resources,
                join_config=join_config,
            )
            await idempotency.set(
                request.session_id,
                "prewarm",
                key,
                {"runtime_state": runtime_state, "join_config": join_config},
            )
            return result

    @trace_async_span(span_names.SESSION_START_LIVE)
    async def start_live_session(
        self, request: StartLiveSessionRequest
    ) -> LiveSessionStartResult:
        session = await self._load_session(request.organization_id, request.session_id)
        if SessionStatus(session.status) in {
            SessionStatus.ENDING,
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        }:
            raise StateTransitionError(
                f"Cannot start session from {session.status}.",
                code="invalid_session_transition",
            )
        if SessionStatus(session.status) == SessionStatus.CREATED:
            await self.prewarm_session(
                PrewarmSessionRequest(
                    organization_id=request.organization_id,
                    session_id=request.session_id,
                    trace_id=request.trace_id,
                    idempotency_key=f"{request.idempotency_key or 'start'}:prewarm",
                )
            )
            session = await self._load_session(request.organization_id, request.session_id)
        await self._audit.audit(
            self._db,
            principal=self._principal,
            action="session.live_start.requested",
            resource_type="demo_session",
            resource_id=request.session_id,
        )
        state = await self.get_orchestration_state(request.organization_id, request.session_id)
        if state.voice_session_id is None:
            voice = await self._prewarm_voice(
                request.organization_id,
                session.product_id,
                request.session_id,
                request.trace_id,
            )
            join_config = sanitize_join_config(voice.join_config)
        else:
            join_config = sanitize_join_config(
                await self._legacy_join_config(request.organization_id, request.session_id)
            )
        await self._publish(
            "session.live.starting",
            request.session_id,
            request.trace_id,
            {"status": session.status},
        )
        greeting = False
        runtime_state = "waiting_for_user"
        if request.transport_connected:
            session = await self._set_session_status(
                session,
                status=SessionStatus.LIVE,
                phase=DemoPhase.OVERVIEW,
                trace_id=request.trace_id,
                event_type="session.live.started",
            )
            await self._audit.audit(
                self._db,
                principal=self._principal,
                action="session.live_start.completed",
                resource_type="demo_session",
                resource_id=request.session_id,
            )
            if get_settings().live_start_greeting_enabled and state.voice_session_id is not None:
                greeting = await self._agent.send_greeting(
                    voice_session_id=state.voice_session_id,
                    greeting_text=get_settings().live_start_greeting_text,
                    trace_id=request.trace_id,
                )
                await self._publish(
                    "agent.greeting.started",
                    request.session_id,
                    request.trace_id,
                    {"voice_session_id": str(state.voice_session_id)},
                )
            runtime_state = "live"
        else:
            await self._publish(
                "session.waiting_for_user",
                request.session_id,
                request.trace_id,
                {"status": "waiting_for_user"},
            )
        await self._db.commit()
        return LiveSessionStartResult(
            session_id=request.session_id,
            status=session.status,
            runtime_state=cast(Any, runtime_state),
            join_config=join_config,
            greeting_dispatched=greeting,
        )

    @trace_async_span(span_names.SESSION_RECOVERY)
    async def recover_session(self, request: RecoverSessionRequest) -> RecoveryResult:
        owner_id = str(uuid4())
        async with SessionOrchestrationLock(self._redis, request.session_id, owner_id):
            await self._load_session(request.organization_id, request.session_id)
            await self._audit.audit(
                self._db,
                principal=self._principal,
                action="session.recovery.started",
                resource_type="demo_session",
                resource_id=request.session_id,
            )
            state = await self.get_orchestration_state(request.organization_id, request.session_id)
            attempt_count = (state.recovery.attempt_count + 1) if state.recovery else 1
            await self._publish(
                "session.recovery.started",
                request.session_id,
                request.trace_id,
                {"reason_code": request.reason_code, "attempt_count": attempt_count},
            )
            decision = decide_recovery_action(
                reason_code=request.reason_code,
                attempt_count=attempt_count,
                max_attempts=get_settings().recovery_max_attempts,
                screen_available=state.browser_session_id is not None,
                go_back_allowed=get_settings().recovery_go_back_allowed,
                navigate_home_allowed=get_settings().recovery_navigate_home_allowed,
            )
            recovered = decision.decision in {"read_current_screen", "go_back", "navigate_home"}
            if decision.decision == "read_current_screen" and state.browser_session_id is not None:
                session = await self._load_session(request.organization_id, request.session_id)
                screen = await self._browser.read_current_screen(
                    organization_id=request.organization_id,
                    product_id=session.product_id,
                    session_id=request.session_id,
                    browser_session_id=state.browser_session_id,
                    url=session.start_url,
                    trace_id=request.trace_id,
                )
                await self._write_screen_state(request.session_id, screen)
                await self._publish(
                    "session.recovery.screen_read",
                    request.session_id,
                    request.trace_id,
                    {"screen_id": str(screen.screen["screen_id"])},
                )
            elif decision.decision == "go_back" and state.browser_session_id is not None:
                await self._browser.go_back(
                    browser_session_id=state.browser_session_id, trace_id=request.trace_id
                )
                await self._publish(
                    "session.recovery.go_back_attempted",
                    request.session_id,
                    request.trace_id,
                    {"reason_code": request.reason_code},
                )
            event_type = "session.recovery.resolved" if recovered else "session.recovery.needs_user"
            await self._publish(
                event_type,
                request.session_id,
                request.trace_id,
                {"decision": decision.decision, "safe_message": decision.safe_message},
            )
            recovery_state = RecoveryState(
                session_id=request.session_id,
                active=not recovered,
                reason_code=request.reason_code,
                attempt_count=attempt_count,
                max_attempts=get_settings().recovery_max_attempts,
                started_at=state.recovery.started_at if state.recovery else utc_now(),
                last_attempt_at=utc_now(),
                last_action=decision.decision,
                resolved=recovered,
            )
            await self._write_state_from_existing(state, recovery=recovery_state, status="recovery")
            await self._audit.audit(
                self._db,
                principal=self._principal,
                action="session.recovery.completed",
                resource_type="demo_session",
                resource_id=request.session_id,
            )
            await self._db.commit()
            return RecoveryResult(
                session_id=request.session_id,
                recovered=recovered,
                decision=decision.decision,
                attempt_count=attempt_count,
                reason_code=request.reason_code,
                safe_message=decision.safe_message,
            )

    @trace_async_span(span_names.SESSION_SHUTDOWN)
    async def shutdown_session(self, request: ShutdownSessionRequest) -> ShutdownSessionResult:
        owner_id = str(uuid4())
        async with SessionOrchestrationLock(self._redis, request.session_id, owner_id):
            session = await self._load_session(request.organization_id, request.session_id)
            if SessionStatus(session.status) == SessionStatus.COMPLETED:
                return ShutdownSessionResult(
                    session_id=request.session_id,
                    status=session.status,
                    completed_with_warnings=False,
                    resources_released=(),
                    summary_status="already_completed",
                    warnings=(),
                )
            await self._audit.audit(
                self._db,
                principal=self._principal,
                action="session.shutdown.requested",
                resource_type="demo_session",
                resource_id=request.session_id,
            )
            await self._publish(
                "session.ending",
                request.session_id,
                request.trace_id,
                {"reason": request.reason or ""},
            )
            active_resources = await self._resource_repo().list_active(
                organization_id=request.organization_id,
                session_id=request.session_id,
            )
            resources = tuple(
                SessionResource(
                    resource_type=row.resource_type,
                    resource_id=row.resource_id,
                    provider=row.provider,
                    status=row.status,
                    metadata=row.metadata_json or {},
                )
                for row in active_resources
            )
            cleanup = ResourceCleanup(
                browser_client=self._browser,
                agent_client=self._agent,
                learner_client=self._learner,
            )
            released: list[str] = []
            warnings: list[str] = []
            for resource in ordered_cleanup_resources(resources):
                row = next(
                    item
                    for item in active_resources
                    if item.resource_type == resource.resource_type
                    and item.resource_id == resource.resource_id
                )
                await self._resource_repo().mark_status(row, status="releasing")
                ok = await cleanup.release(resource, trace_id=request.trace_id)
                if ok:
                    await self._resource_repo().mark_status(row, status="released")
                    released.append(resource.resource_type)
                else:
                    await self._resource_repo().mark_status(
                        row, status="release_failed", error_code="release_failed"
                    )
                    warnings.append(f"{resource.resource_type}_release_failed")
            session = await self._set_session_status(
                session,
                status=SessionStatus.COMPLETED,
                phase=DemoPhase.COMPLETED,
                trace_id=request.trace_id,
                event_type="session.ended" if not warnings else "session.completed_with_warnings",
                ended=True,
            )
            summary = deterministic_summary_payload(session_id=request.session_id)
            await self._publish(
                "lead_summary.ready",
                request.session_id,
                request.trace_id,
                {"summary": summary},
            )
            await self._audit.audit(
                self._db,
                principal=self._principal,
                action="session.shutdown.completed",
                resource_type="demo_session",
                resource_id=request.session_id,
            )
            await self._db.commit()
            return ShutdownSessionResult(
                session_id=request.session_id,
                status=session.status,
                completed_with_warnings=bool(warnings),
                resources_released=tuple(released),
                summary_status="deterministic_ready",
                warnings=tuple(warnings),
            )

    async def get_orchestration_state(
        self, organization_id: UUID, session_id: UUID
    ) -> OrchestrationState:
        cached = await OrchestrationStateStore(self._redis).get_state(session_id)
        if cached is not None and cached.organization_id == organization_id:
            return cached
        session = await self._load_session(organization_id, session_id)
        resources = tuple(
            SessionResource(
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                provider=row.provider,
                status=row.status,
                metadata=row.metadata_json or {},
            )
            for row in await self._resource_repo().list_for_session(
                organization_id=organization_id, session_id=session_id
            )
        )
        readiness = compute_readiness(
            browser_session_ready=any(
                resource.resource_type == "browser_session" and resource.status == "ready"
                for resource in resources
            ),
            url_loaded=any(resource.resource_type == "browser_session" for resource in resources),
            first_screen_read=any(
                resource.resource_type == "browser_session" and resource.status == "ready"
                for resource in resources
            ),
            safe_action_count=len(await LiveStateStore(self._redis).get_safe_actions(session_id)),
            voice_session_ready=any(
                resource.resource_type == "voice_session" and resource.status == "ready"
                for resource in resources
            ),
            join_config_ready=any(
                resource.resource_type == "voice_session" for resource in resources
            ),
            recipe_compiled=any(
                resource.resource_type == "compiled_recipe" for resource in resources
            )
            or session.recipe_id is None,
            learner_enqueued=any(resource.resource_type == "learner_run" for resource in resources),
            provider_warmed_count=3,
        )
        return OrchestrationState(
            organization_id=organization_id,
            session_id=session_id,
            product_id=session.product_id,
            status=session.status,
            browser_session_id=_resource_uuid(resources, "browser_session"),
            voice_session_id=_resource_uuid(resources, "voice_session"),
            transport_session_id=_resource_id(resources, "transport_session"),
            learner_run_id=_resource_uuid(resources, "learner_run"),
            compiled_recipe_id=_resource_uuid(resources, "compiled_recipe"),
            readiness=readiness,
            recovery=None,
            resources=resources,
            updated_at=utc_now(),
        )

    async def _prewarm_browser(
        self, session: DemoSessionRow, trace_id: str
    ) -> BrowserScreenResult:
        created = await self._browser.create_session(
            organization_id=session.organization_id,
            product_id=session.product_id,
            session_id=session.session_id,
            start_url=session.start_url,
            trace_id=trace_id,
        )
        await self._browser.navigate(
            browser_session_id=created.browser_session_id,
            url=session.start_url,
            trace_id=trace_id,
        )
        screen = await self._browser.read_current_screen(
            organization_id=session.organization_id,
            product_id=session.product_id,
            session_id=session.session_id,
            browser_session_id=created.browser_session_id,
            url=session.start_url,
            trace_id=trace_id,
        )
        await self._write_screen_state(session.session_id, screen)
        return screen

    async def _prewarm_voice(
        self,
        organization_id: UUID,
        product_id: UUID,
        session_id: UUID,
        trace_id: str,
    ) -> VoiceSessionResult:
        return await self._agent.create_voice_session(
            organization_id=organization_id,
            product_id=product_id,
            session_id=session_id,
            trace_id=trace_id,
        )

    async def _write_screen_state(
        self, session_id: UUID, result: BrowserScreenResult
    ) -> None:
        store = LiveStateStore(self._redis)
        await store.set_current_screen(session_id, cast(dict[str, Any], result.screen))
        await store.set_safe_actions(
            session_id,
            cast(tuple[dict[str, Any], ...], result.safe_actions),
        )
        await store.set_browser_status(
            session_id,
            {
                "browser_session_id": str(result.browser_session_id),
                "status": "ready",
                "current_url": str(result.screen["url"]),
                "updated_at": utc_now().isoformat(),
            },
        )

    async def _compile_recipe_if_needed(
        self, session: DemoSessionRow, trace_id: str
    ) -> UUID | None:
        if session.recipe_id is None:
            return None
        response = await RecipeService().compile_recipe(
            self._db,
            self._redis,
            self._event_bus,
            self._principal,
            session.product_id,
            session.recipe_id,
            self._request_context,
        )
        _ = trace_id
        return UUID(response.compiled_recipe_id)

    async def _persist_prewarm_resources(
        self,
        *,
        session: DemoSessionRow,
        browser_result: BrowserScreenResult | None,
        voice_result: VoiceSessionResult | None,
        learner_run_id: UUID | None,
        compiled_recipe_id: UUID | None,
    ) -> tuple[SessionResource, ...]:
        repo = self._resource_repo()
        resources: list[SessionResource] = []
        if browser_result is not None:
            row = await repo.register(
                organization_id=session.organization_id,
                session_id=session.session_id,
                resource_type="browser_session",
                resource_id=str(browser_result.browser_session_id),
                provider="browser_runtime",
                status="ready",
                metadata={"screen_id": str(browser_result.screen["screen_id"])},
            )
            resources.append(_resource_from_row(row))
        if voice_result is not None:
            row = await repo.register(
                organization_id=session.organization_id,
                session_id=session.session_id,
                resource_type="voice_session",
                resource_id=str(voice_result.voice_session_id),
                provider="agent_runtime",
                status="ready",
                metadata={"transport_session_id": voice_result.transport_session_id},
            )
            resources.append(_resource_from_row(row))
            transport = await repo.register(
                organization_id=session.organization_id,
                session_id=session.session_id,
                resource_type="transport_session",
                resource_id=voice_result.transport_session_id,
                provider="small_webrtc",
                status="ready",
                metadata={},
            )
            resources.append(_resource_from_row(transport))
        if learner_run_id is not None:
            row = await repo.register(
                organization_id=session.organization_id,
                session_id=session.session_id,
                resource_type="learner_run",
                resource_id=str(learner_run_id),
                provider="learner_worker",
                status="ready",
                metadata={"detached": True},
            )
            resources.append(_resource_from_row(row))
        if compiled_recipe_id is not None:
            row = await repo.register(
                organization_id=session.organization_id,
                session_id=session.session_id,
                resource_type="compiled_recipe",
                resource_id=str(compiled_recipe_id),
                provider="recipe_engine",
                status="ready",
                metadata={},
            )
            resources.append(_resource_from_row(row))
        row = await repo.register(
            organization_id=session.organization_id,
            session_id=session.session_id,
            resource_type="redis_live_state",
            resource_id=str(session.session_id),
            provider="redis",
            status="ready",
            metadata={},
        )
        resources.append(_resource_from_row(row))
        return tuple(resources)

    async def _set_session_status(
        self,
        session: DemoSessionRow,
        *,
        status: SessionStatus,
        phase: DemoPhase,
        trace_id: str,
        event_type: str,
        ended: bool = False,
    ) -> DemoSessionRow:
        current = SessionStatus(session.status)
        if current != status:
            _validate_transition(current, status)
        updated = await DemoSessionRepository(self._db).set_status(
            organization_id=session.organization_id,
            session_id=session.session_id,
            status=status,
            current_phase=phase,
            started_at=(
                utc_now()
                if status in {SessionStatus.PREWARMING, SessionStatus.LIVE}
                else None
            ),
            ended_at=(
                utc_now()
                if ended or status in {SessionStatus.COMPLETED, SessionStatus.FAILED}
                else None
            ),
        )
        if updated is None:
            raise NotFoundError("Session not found.", code="session_not_found")
        await SessionLifecycleEventRepository(self._db).append(
            organization_id=session.organization_id,
            session_id=session.session_id,
            event_type=event_type,
            previous_status=current.value,
            next_status=status.value,
            trace_id=trace_id,
        )
        await self._publish(event_type, session.session_id, trace_id, {"status": status.value})
        return updated

    async def _write_state(
        self,
        *,
        session: DemoSessionRow,
        readiness: ReadinessState,
        resources: tuple[SessionResource, ...],
        browser_session_id: UUID | None,
        voice_session_id: UUID | None,
        transport_session_id: str | None,
        learner_run_id: UUID | None,
        compiled_recipe_id: UUID | None,
        runtime_state: str,
    ) -> None:
        state = OrchestrationState(
            organization_id=session.organization_id,
            session_id=session.session_id,
            product_id=session.product_id,
            status=runtime_state,
            browser_session_id=browser_session_id,
            voice_session_id=voice_session_id,
            transport_session_id=transport_session_id,
            learner_run_id=learner_run_id,
            compiled_recipe_id=compiled_recipe_id,
            readiness=readiness,
            recovery=None,
            resources=resources,
            updated_at=utc_now(),
        )
        await OrchestrationStateStore(self._redis).set_state(state)

    async def _write_state_from_existing(
        self,
        state: OrchestrationState,
        *,
        recovery: RecoveryState | None,
        status: str,
    ) -> None:
        await OrchestrationStateStore(self._redis).set_state(
            OrchestrationState(
                organization_id=state.organization_id,
                session_id=state.session_id,
                product_id=state.product_id,
                status=status,
                browser_session_id=state.browser_session_id,
                voice_session_id=state.voice_session_id,
                transport_session_id=state.transport_session_id,
                learner_run_id=state.learner_run_id,
                compiled_recipe_id=state.compiled_recipe_id,
                readiness=state.readiness,
                recovery=recovery,
                resources=state.resources,
                updated_at=utc_now(),
            )
        )

    async def _load_session(self, organization_id: UUID, session_id: UUID) -> DemoSessionRow:
        session = await DemoSessionRepository(self._db).get_session(
            organization_id=organization_id, session_id=session_id
        )
        if session is None:
            raise NotFoundError("Session not found.", code="session_not_found")
        return session

    async def _publish(
        self, event_type: str, session_id: UUID, trace_id: str, payload: dict[str, object]
    ) -> None:
        _ = trace_id
        await publish_orchestration_event(
            self._event_bus,
            organization_id=self._principal.organization_id,
            session_id=session_id,
            event_type=event_type,
            request_context=self._request_context,
            payload=payload,
        )

    async def _legacy_join_config(
        self, organization_id: UUID, session_id: UUID
    ) -> dict[str, object]:
        join_config = await self._join_config.get_join_config(
            organization_id=organization_id, session_id=session_id
        )
        return cast(dict[str, object], join_config.model_dump(mode="json"))

    def _resource_repo(self) -> SessionResourceAllocationRepository:
        return SessionResourceAllocationRepository(self._db)


def _validate_transition(current: SessionStatus, next_: SessionStatus) -> None:
    allowed = {
        SessionStatus.CREATED: {
            SessionStatus.PREWARMING,
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        },
        SessionStatus.PREWARMING: {
            SessionStatus.WAITING_FOR_USER,
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        },
        SessionStatus.WAITING_FOR_USER: {
            SessionStatus.LIVE,
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        },
        SessionStatus.LIVE: {
            SessionStatus.ENDING,
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        },
        SessionStatus.ENDING: {SessionStatus.COMPLETED, SessionStatus.FAILED},
        SessionStatus.COMPLETED: {SessionStatus.COMPLETED},
        SessionStatus.FAILED: {SessionStatus.FAILED, SessionStatus.COMPLETED},
    }
    if next_ not in allowed[current] and next_ != current:
        raise StateTransitionError(
            f"Cannot transition session from {current.value} to {next_.value}.",
            code="invalid_session_transition",
        )


def _resource_from_row(row: Any) -> SessionResource:
    return SessionResource(
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        provider=row.provider,
        status=row.status,
        metadata=row.metadata_json or {},
    )


def _resource_uuid(resources: tuple[SessionResource, ...], resource_type: str) -> UUID | None:
    value = _resource_id(resources, resource_type)
    return UUID(value) if value else None


def _resource_id(resources: tuple[SessionResource, ...], resource_type: str) -> str | None:
    for resource in resources:
        if resource.resource_type == resource_type and resource.status in {"allocated", "ready"}:
            return resource.resource_id
    return None
