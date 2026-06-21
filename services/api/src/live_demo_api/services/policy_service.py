"""Policy service facade for API endpoints and future workers."""

from __future__ import annotations

from live_demo_backend_common.policy.action_policy import ActionPolicyRequest, ActionSafetyPolicy
from live_demo_backend_common.policy.policy_types import PolicyDecision
from live_demo_backend_common.policy.rbac import RbacPolicy
from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine


class PolicyService:
    def __init__(
        self,
        *,
        action_policy: ActionSafetyPolicy | None = None,
        rbac_policy: RbacPolicy | None = None,
        redaction_engine: RedactionEngine | None = None,
    ) -> None:
        self._action_policy = action_policy or ActionSafetyPolicy()
        self._rbac_policy = rbac_policy or RbacPolicy()
        self._redaction = redaction_engine or RedactionEngine()

    def evaluate_action(self, request: ActionPolicyRequest) -> PolicyDecision:
        return self._action_policy.evaluate(request)

    @property
    def rbac(self) -> RbacPolicy:
        return self._rbac_policy

    def redact_prompt_text(self, text: str) -> str:
        return str(self._redaction.redact_text(text, RedactionContext.PROMPT).redacted_value)
