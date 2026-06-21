"""Pipeline wrapper around structured output validation."""

from live_demo_agent_runtime.agent_brain.agent_decision import AgentDecision
from live_demo_agent_runtime.agent_brain.output_validator import AgentOutputValidator
from live_demo_agent_runtime.context.context_types import RealtimeAgentContext


class AgentDecisionProcessor:
    def __init__(self, validator: AgentOutputValidator) -> None:
        self._validator = validator

    def process(self, raw_output: str, context: RealtimeAgentContext) -> AgentDecision:
        return self._validator.validate(raw_output, context)
