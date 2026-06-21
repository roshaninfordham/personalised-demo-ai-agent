"""Browser tool routing request/result types."""

from dataclasses import dataclass
from uuid import UUID

from live_demo_agent_runtime.agent_brain.agent_decision import AgentDecision
from live_demo_agent_runtime.context.context_types import RealtimeAgentContext


@dataclass(frozen=True, slots=True)
class ToolRouteRequest:
    organization_id: UUID
    demo_session_id: UUID
    product_id: UUID
    active_turn_id: UUID
    agent_decision: AgentDecision
    current_context: RealtimeAgentContext
    trace_id: str


@dataclass(frozen=True, slots=True)
class ToolRouteResult:
    executed: bool
    tool_name: str | None
    action_id: str | None
    success: bool | None
    policy_decision: str | None
    risk_level: str | None
    browser_action_result: dict[str, object] | None
    error_code: str | None
    error_message: str | None
    latency_ms: int
