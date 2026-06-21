"""Agent-runtime action policy wrapper."""

from __future__ import annotations

from live_demo_backend_common.policy.action_policy import ActionPolicyRequest, ActionSafetyPolicy
from live_demo_backend_common.policy.policy_types import PolicyDecision


class AgentActionPolicy:
    def __init__(self, policy: ActionSafetyPolicy | None = None) -> None:
        self._policy = policy or ActionSafetyPolicy()

    def evaluate(self, request: ActionPolicyRequest) -> PolicyDecision:
        return self._policy.evaluate(request)

