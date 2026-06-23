"""Deterministic turn planner for local/fake-provider demos.

The production LLM path should produce the same shape after model validation. This
planner keeps default local mode useful without paid APIs and, more importantly,
keeps auth, safety, and action routing explicit instead of letting a prompt or UI
placeholder imply progress that did not happen.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AgenticPhase(StrEnum):
    INIT = "INIT"
    AUTH_HANDLING = "AUTH_HANDLING"
    DISCOVERY = "DISCOVERY"
    SCREEN_ORIENTATION = "SCREEN_ORIENTATION"
    GUIDED_NAVIGATION = "GUIDED_NAVIGATION"
    QUESTION_ANSWERING = "QUESTION_ANSWERING"
    RECOVERY = "RECOVERY"
    SUMMARY = "SUMMARY"
    END = "END"


@dataclass(frozen=True, slots=True)
class TurnDecision:
    phase: AgenticPhase
    response: str
    action: dict[str, object] | None = None
    blocked: bool = False
    action_type: str | None = None
    label: str | None = None
    reason_code: str = "screen_grounded_response"

    def as_router_payload(self) -> dict[str, object]:
        return {
            "phase": self.phase.value,
            "response": self.response,
            "action": self.action,
            "blocked": self.blocked,
            "action_type": self.action_type,
            "label": self.label,
            "reason_code": self.reason_code,
        }


def plan_text_turn(
    user_text: str,
    screen: dict[str, object],
    safe_actions: list[dict[str, object]],
) -> TurnDecision:
    lowered = user_text.lower()
    title = str(screen.get("title") or "the current screen")
    summary = str(screen.get("summary") or f"I can see {title}.")
    auth_state = screen.get("auth_state") if isinstance(screen.get("auth_state"), dict) else {}
    login_required = (
        bool(auth_state.get("login_required")) if isinstance(auth_state, dict) else False
    )

    if _contains_any(lowered, ("end demo", "stop demo", "that's all", "wrap up")):
        return TurnDecision(
            phase=AgenticPhase.SUMMARY,
            response=(
                "I can wrap up here. I will summarize only what was actually shown and any "
                "open questions from this session."
            ),
            reason_code="user_requested_summary",
        )

    if _contains_any(lowered, ("delete", "remove", "billing", "payment", "purchase", "upgrade")):
        return TurnDecision(
            phase=AgenticPhase.AUTH_HANDLING if login_required else AgenticPhase.GUIDED_NAVIGATION,
            response=(
                "I cannot perform destructive, billing, or payment actions in a live demo. "
                "I can keep showing safe product workflows instead."
            ),
            blocked=True,
            action_type="blocked_action",
            label="Dangerous action",
            reason_code="dangerous_action_blocked",
        )

    if login_required:
        return _plan_auth_turn(lowered, safe_actions)

    if _contains_any(lowered, ("salesforce", "soc2", "soc 2", "hipaa", "pricing", "sso")):
        return TurnDecision(
            phase=AgenticPhase.QUESTION_ANSWERING,
            response=(
                "I cannot verify that from the current screen. "
                f"What I can verify is: {summary}"
            ),
            reason_code="unsupported_claim_avoided",
        )

    if _contains_any(lowered, ("metric", "create", "add")):
        action = _find_action(safe_actions, ("add metric", "create metric", "new metric", "metric"))
        return TurnDecision(
            phase=AgenticPhase.GUIDED_NAVIGATION,
            response=(
                "I will focus on the metric creation workflow and highlight the safest "
                "matching control."
            ),
            action=action,
            action_type=str(action.get("action_type")) if action else None,
            label=str(action.get("label")) if action else None,
            reason_code="metric_workflow_requested",
        )

    if "report" in lowered:
        action = _find_action(safe_actions, ("reports", "reporting", "analytics"))
        return TurnDecision(
            phase=AgenticPhase.GUIDED_NAVIGATION,
            response="I will show the reporting area if it is available on this screen.",
            action=action,
            action_type=str(action.get("action_type")) if action else None,
            label=str(action.get("label")) if action else None,
            reason_code="reporting_requested",
        )

    action = _find_action(safe_actions, ("dashboard", "overview", "read current screen")) or (
        safe_actions[0] if safe_actions else None
    )
    return TurnDecision(
        phase=AgenticPhase.SCREEN_ORIENTATION,
        response=(
            f"From the visible screen, {summary} "
            "I will start by orienting you around this view."
        ),
        action=action,
        action_type=str(action.get("action_type")) if action else None,
        label=str(action.get("label")) if action else None,
        reason_code="screen_orientation",
    )


def _plan_auth_turn(lowered: str, safe_actions: list[dict[str, object]]) -> TurnDecision:
    if _contains_any(lowered, ("sign up", "signup", "create account", "register")):
        action = _find_action(safe_actions, ("sign up", "sign-up", "create account", "register"))
        safe_action = _safe_auth_navigation_action(action)
        return TurnDecision(
            phase=AgenticPhase.AUTH_HANDLING,
            response=(
                "I am at the sign-in screen, so I cannot verify the in-app workflow yet. "
                "I can show the sign-up path without submitting anything; I will open "
                "the visible sign-up link if it is available."
            ),
            action=safe_action,
            action_type=str(action.get("action_type")) if action else None,
            label=str(action.get("label")) if action else None,
            reason_code="auth_signup_tutorial",
        )
    return TurnDecision(
        phase=AgenticPhase.AUTH_HANDLING,
        response=(
            "This product is currently showing a sign-in screen, so I cannot verify the "
            "authenticated app yet. You can sign in securely, or I can explain the visible "
            "login and sign-up flow without entering or storing credentials."
        ),
        reason_code="auth_required",
    )


def _find_action(
    safe_actions: list[dict[str, object]],
    labels: tuple[str, ...],
) -> dict[str, object] | None:
    for action in safe_actions:
        label = str(action.get("label") or "").lower()
        if any(candidate in label for candidate in labels):
            return action
    return None


def _safe_auth_navigation_action(action: dict[str, object] | None) -> dict[str, object] | None:
    if action is None:
        return None
    label = str(action.get("label") or "").lower()
    action_type = str(action.get("action_type") or "")
    if "sign in" in label or "log in" in label or action_type == "type_into_element":
        return None
    return action


def _contains_any(value: str, candidates: tuple[str, ...]) -> bool:
    return any(candidate in value for candidate in candidates)
