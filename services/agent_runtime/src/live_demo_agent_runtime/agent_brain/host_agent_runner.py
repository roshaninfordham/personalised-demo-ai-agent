"""Realtime host-agent turn runner."""

import time
from dataclasses import dataclass
from uuid import UUID, uuid4

from live_demo_agent_runtime.agent_brain.agent_decision import (
    AgentDecision,
    MemoryUpdateDecision,
)
from live_demo_agent_runtime.agent_brain.host_agent import build_host_agent_request
from live_demo_agent_runtime.agent_brain.output_validator import (
    AgentOutputValidationError,
    AgentOutputValidator,
)
from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.context.context_types import (
    BuildRealtimeContextRequest,
    RealtimeAgentContext,
)
from live_demo_agent_runtime.context.realtime_context_builder import RealtimeContextBuilder
from live_demo_agent_runtime.events import event_types
from live_demo_agent_runtime.events.event_publisher import EventPublisher
from live_demo_agent_runtime.memory.memory_types import MemoryUpdate
from live_demo_agent_runtime.memory.memory_update_handler import MemoryUpdateHandler
from live_demo_agent_runtime.persona.persona_tracker import PersonaTracker
from live_demo_agent_runtime.persona.persona_types import PersonaState
from live_demo_agent_runtime.tools.browser_tool_results import ToolRouteRequest, ToolRouteResult
from live_demo_agent_runtime.tools.browser_tool_router import BrowserToolRouter
from live_demo_backend_common.ai.text.base import TextGenerationProvider


@dataclass(frozen=True, slots=True)
class AgentTurnRequest:
    organization_id: UUID
    demo_session_id: UUID
    product_id: UUID
    user_utterance: str
    user_transcript_event_id: UUID | None
    active_turn_id: UUID
    trace_id: str
    persona_state: PersonaState | None = None
    fake_llm_response: str | None = None


@dataclass(frozen=True, slots=True)
class AgentTurnResult:
    decision: AgentDecision
    context: RealtimeAgentContext
    tool_result: ToolRouteResult | None
    persona_state: PersonaState
    latency_ms: int
    used_fallback: bool


class HostAgentRunner:
    def __init__(
        self,
        *,
        settings: AgentRuntimeSettings,
        context_builder: RealtimeContextBuilder,
        text_provider: TextGenerationProvider,
        output_validator: AgentOutputValidator,
        persona_tracker: PersonaTracker,
        memory_handler: MemoryUpdateHandler,
        tool_router: BrowserToolRouter,
        event_publisher: EventPublisher,
    ) -> None:
        self._settings = settings
        self._context_builder = context_builder
        self._text_provider = text_provider
        self._output_validator = output_validator
        self._persona_tracker = persona_tracker
        self._memory_handler = memory_handler
        self._tool_router = tool_router
        self._event_publisher = event_publisher

    async def run_turn(self, request: AgentTurnRequest) -> AgentTurnResult:
        started = time.perf_counter_ns()
        await self._event_publisher.publish(
            organization_id=request.organization_id,
            demo_session_id=request.demo_session_id,
            event_type=event_types.AGENT_TURN_STARTED,
            trace_id=request.trace_id,
            payload={"turn_id": str(request.active_turn_id)},
        )
        context = await self._context_builder.build_context(
            BuildRealtimeContextRequest(
                organization_id=request.organization_id,
                demo_session_id=request.demo_session_id,
                product_id=request.product_id,
                user_utterance=request.user_utterance,
                user_transcript_event_id=request.user_transcript_event_id,
                active_turn_id=request.active_turn_id,
                trace_id=request.trace_id,
            )
        )
        persona_state = request.persona_state or self._persona_tracker.initial_state()
        persona_state = self._persona_tracker.update(persona_state, request.user_utterance)
        provider_request = build_host_agent_request(
            context=context,
            settings=self._settings,
            request_id=str(uuid4()),
            trace_id=request.trace_id,
            fake_response=request.fake_llm_response,
        )
        used_fallback = False
        response = await self._text_provider.generate(provider_request)
        try:
            decision = self._output_validator.validate(response.content, context)
        except AgentOutputValidationError:
            used_fallback = True
            decision = self._output_validator.fallback_decision(context)
        memory_updates = tuple(
            _memory_decision_to_update(update) for update in decision.memory_updates
        )
        await self._memory_handler.handle_updates(
            organization_id=request.organization_id,
            demo_session_id=request.demo_session_id,
            updates=memory_updates,
            trace_id=request.trace_id,
        )
        tool_result: ToolRouteResult | None = None
        if decision.browser_action is not None:
            tool_result = await self._tool_router.route(
                ToolRouteRequest(
                    organization_id=request.organization_id,
                    demo_session_id=request.demo_session_id,
                    product_id=request.product_id,
                    active_turn_id=request.active_turn_id,
                    agent_decision=decision,
                    current_context=context,
                    trace_id=request.trace_id,
                )
            )
        latency_ms = int((time.perf_counter_ns() - started) / 1_000_000)
        await self._event_publisher.publish(
            organization_id=request.organization_id,
            demo_session_id=request.demo_session_id,
            event_type=event_types.AGENT_TURN_COMPLETED,
            trace_id=request.trace_id,
            payload={
                "turn_id": str(request.active_turn_id),
                "latency_ms": latency_ms,
                "used_fallback": used_fallback,
                "browser_action_id": (
                    decision.browser_action.action_id
                    if decision.browser_action is not None
                    else None
                ),
            },
        )
        return AgentTurnResult(
            decision=decision,
            context=context,
            tool_result=tool_result,
            persona_state=persona_state,
            latency_ms=latency_ms,
            used_fallback=used_fallback,
        )


def _memory_decision_to_update(update: MemoryUpdateDecision) -> MemoryUpdate:
    return MemoryUpdate(
        type=update.type,
        content=update.content,
        confidence=update.confidence,
        importance=update.importance,
        evidence_transcript_event_ids=tuple(
            UUID(item) for item in update.evidence.transcript_event_ids
        ),
        evidence_screen_ids=tuple(update.evidence.screen_ids),
        evidence_action_ids=tuple(update.evidence.action_ids),
    )
