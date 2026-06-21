"""Validate strict agent JSON output against context and safety rules."""

import json
from collections.abc import Iterable

from pydantic import ValidationError

from live_demo_agent_runtime.agent_brain.agent_decision import AgentDecision
from live_demo_agent_runtime.agent_brain.json_repair import strip_json_code_fence
from live_demo_agent_runtime.context.context_packager import render_context_json
from live_demo_agent_runtime.context.context_types import RealtimeAgentContext
from live_demo_agent_runtime.errors import AgentRuntimeError

FORBIDDEN_ACTION_STRINGS = (
    "document.",
    "window.",
    "queryselector",
    "getelementbyid",
    "xpath",
    "evaluate(",
    "<script",
    "javascript:",
)

CLAIM_KEYWORD_GROUPS: dict[str, tuple[str, ...]] = {
    "integration": ("integration", "integrate", "salesforce", "hubspot", "crm"),
    "pricing": ("pricing", "price", "cost", "plan"),
    "security": ("security", "encryption", "compliance", "soc2", "hipaa", "gdpr"),
    "api": ("api", "webhook"),
    "export": ("export", "download", "csv"),
}


class AgentOutputValidationError(AgentRuntimeError):
    def __init__(self, safe_message: str, code: str = "agent_output_invalid") -> None:
        super().__init__(code, safe_message, 422)


class AgentOutputValidator:
    def validate(self, raw_output: str, context: RealtimeAgentContext) -> AgentDecision:
        try:
            parsed = json.loads(strip_json_code_fence(raw_output))
        except json.JSONDecodeError as exc:
            raise AgentOutputValidationError("Agent output was not valid JSON.") from exc
        try:
            decision = AgentDecision.model_validate(parsed)
        except ValidationError as exc:
            raise AgentOutputValidationError("Agent output did not match schema.") from exc
        self._validate_browser_action(decision, context)
        self._validate_memory_updates(decision)
        self._validate_grounded_claims(decision, context)
        return decision

    def fallback_decision(self, context: RealtimeAgentContext) -> AgentDecision:
        read_action = next(
            (
                action
                for action in context.safe_actions
                if action.action_type == "read_current_screen"
                or action.action_id == "act_read_current_screen"
            ),
            None,
        )
        browser_action = (
            {
                "action_id": read_action.action_id,
                "tool_name": "read_current_screen",
                "reason": "Fallback after invalid structured model output.",
            }
            if read_action is not None
            else None
        )
        return AgentDecision.model_validate(
            {
                "spoken_response": (
                    "I'm sorry, I need a moment to stay grounded. "
                    "Let me re-check the current screen."
                ),
                "browser_action": browser_action,
                "memory_updates": [],
                "confidence": 0.2,
            }
        )

    def _validate_browser_action(
        self,
        decision: AgentDecision,
        context: RealtimeAgentContext,
    ) -> None:
        if decision.browser_action is None:
            return
        raw = decision.browser_action.model_dump_json().lower()
        if any(marker in raw for marker in FORBIDDEN_ACTION_STRINGS):
            raise AgentOutputValidationError("Agent output requested forbidden browser authority.")
        actions = {action.action_id: action for action in context.safe_actions}
        action = actions.get(decision.browser_action.action_id)
        if action is None:
            raise AgentOutputValidationError("Agent selected an unknown action_id.")
        if action.risk_level == "blocked":
            raise AgentOutputValidationError("Agent selected a blocked action.")
        if action.risk_level == "high" and not action.requires_confirmation:
            raise AgentOutputValidationError("High-risk action policy is inconsistent.")
        if not _tool_matches_action(decision.browser_action.tool_name, action.action_type):
            raise AgentOutputValidationError("Agent selected a tool that does not match action.")

    def _validate_memory_updates(self, decision: AgentDecision) -> None:
        for update in decision.memory_updates:
            if not update.evidence.has_any():
                raise AgentOutputValidationError("Memory updates require evidence.")
            if _contains_secret_like_text([update.content]):
                raise AgentOutputValidationError("Memory update looked secret-like.")

    def _validate_grounded_claims(
        self,
        decision: AgentDecision,
        context: RealtimeAgentContext,
    ) -> None:
        response = decision.spoken_response.lower()
        if _is_uncertainty_or_denial(response):
            return
        context_text = render_context_json(context).lower()
        for group_terms in CLAIM_KEYWORD_GROUPS.values():
            if not any(term in response for term in group_terms):
                continue
            if not any(term in context_text for term in group_terms):
                raise AgentOutputValidationError("Agent made an unsupported product claim.")


def _tool_matches_action(tool_name: str, action_type: str) -> bool:
    if tool_name == action_type:
        return True
    if tool_name == "type_demo_text" and action_type in {"type_into_element", "type_demo_text"}:
        return True
    return tool_name == "read_current_screen" and action_type == "read_current_screen"


def _contains_secret_like_text(values: Iterable[str]) -> bool:
    markers = (
        "api_key",
        "password",
        "secret",
        "token",
        "private_key",
        "client_secret",
        "refresh_token",
        "access_token",
        "credit card",
        "ssn",
    )
    return any(marker in value.lower() for value in values for marker in markers)


def _is_uncertainty_or_denial(response: str) -> bool:
    markers = (
        "cannot verify",
        "can't verify",
        "i cannot confirm",
        "i can't confirm",
        "not enough information",
    )
    return any(marker in response for marker in markers)
