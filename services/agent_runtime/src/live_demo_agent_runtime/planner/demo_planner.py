"""Deterministic demo planner state machine."""

from dataclasses import dataclass

from live_demo_agent_runtime.context.context_types import RealtimeAgentContext
from live_demo_agent_runtime.planner.demo_phase import DemoPhase
from live_demo_agent_runtime.planner.phase_transitions import validate_phase_transition
from live_demo_agent_runtime.tools.browser_tool_results import ToolRouteResult


@dataclass(frozen=True, slots=True)
class DemoPlannerState:
    phase: DemoPhase
    discovery_turns: int = 0
    recovery_attempts: int = 0


class DemoPlanner:
    def update(
        self,
        *,
        state: DemoPlannerState,
        user_utterance: str,
        context: RealtimeAgentContext,
        tool_result: ToolRouteResult | None = None,
    ) -> DemoPlannerState:
        next_phase = self._choose_next_phase(
            state=state,
            user_utterance=user_utterance,
            context=context,
            tool_result=tool_result,
        )
        validate_phase_transition(state.phase, next_phase)
        return DemoPlannerState(
            phase=next_phase,
            discovery_turns=(
                state.discovery_turns + 1
                if next_phase == DemoPhase.DISCOVERY
                else state.discovery_turns
            ),
            recovery_attempts=(
                state.recovery_attempts + 1
                if next_phase == DemoPhase.RECOVERY
                else state.recovery_attempts
            ),
        )

    def _choose_next_phase(
        self,
        *,
        state: DemoPlannerState,
        user_utterance: str,
        context: RealtimeAgentContext,
        tool_result: ToolRouteResult | None,
    ) -> DemoPhase:
        normalized = user_utterance.lower()
        if tool_result is not None and tool_result.success is False:
            return DemoPhase.RECOVERY
        if any(term in normalized for term in ("stop", "end demo", "that's all")):
            return DemoPhase.END if state.phase == DemoPhase.SUMMARY else DemoPhase.SUMMARY
        if any(term in normalized for term in ("thanks", "thank you")):
            return DemoPhase.SUMMARY
        if "?" in user_utterance or any(
            term in normalized for term in ("does", "can", "what", "how", "why")
        ):
            return DemoPhase.Q_AND_A
        if state.phase == DemoPhase.START:
            return DemoPhase.OVERVIEW if context.current_screen is not None else DemoPhase.DISCOVERY
        if state.phase == DemoPhase.DISCOVERY and state.discovery_turns >= 1:
            return DemoPhase.OVERVIEW
        if state.phase == DemoPhase.OVERVIEW and context.safe_actions:
            return DemoPhase.CORE_WORKFLOW
        return state.phase
