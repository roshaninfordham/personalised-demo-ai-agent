"""Deterministic recovery decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    decision: str
    safe_message: str
    severity: str
    reason_codes: tuple[str, ...]
    fatal: bool = False


def classify_recovery_reason(reason_code: str) -> str:
    if reason_code in {"stale_element", "screen_read_timeout"}:
        return "low"
    if reason_code in {"unexpected_screen", "navigation_blocked", "action_failed"}:
        return "medium"
    if reason_code in {"browser_session_crashed", "high_risk_screen"}:
        return "high"
    if reason_code in {"session_security_violation", "cannot_create_browser_replacement"}:
        return "fatal"
    return "medium"


def decide_recovery_action(
    *,
    reason_code: str,
    attempt_count: int,
    max_attempts: int,
    screen_available: bool,
    go_back_allowed: bool,
    navigate_home_allowed: bool,
) -> RecoveryDecision:
    severity = classify_recovery_reason(reason_code)
    if severity == "fatal" or attempt_count > max_attempts:
        return RecoveryDecision(
            decision="enter_degraded_mode",
            safe_message=(
                "I can't safely recover the browser state, so I'll avoid clicking further."
            ),
            severity=severity,
            reason_codes=("recovery_attempts_exceeded",)
            if attempt_count > max_attempts
            else ("fatal_recovery_reason",),
            fatal=severity == "fatal",
        )
    if not screen_available:
        return RecoveryDecision(
            decision="read_current_screen",
            safe_message=(
                "I'm going to re-check the current screen so I don't click the wrong thing."
            ),
            severity=severity,
            reason_codes=("screen_missing",),
        )
    if reason_code in {"stale_element", "screen_read_timeout", "action_failed"}:
        return RecoveryDecision(
            decision="read_current_screen",
            safe_message=(
                "I'm going to re-check the current screen so I don't click the wrong thing."
            ),
            severity=severity,
            reason_codes=("refresh_screen_state",),
        )
    if reason_code == "high_risk_screen" and go_back_allowed:
        return RecoveryDecision(
            decision="go_back",
            safe_message=(
                "This looks like a risky area, so I'll safely go back before continuing."
            ),
            severity=severity,
            reason_codes=("high_risk_screen_go_back",),
        )
    if reason_code in {"unexpected_screen", "navigation_blocked"} and go_back_allowed:
        return RecoveryDecision(
            decision="go_back",
            safe_message=(
                "That didn't land where I expected, so I'll safely go back and reorient."
            ),
            severity=severity,
            reason_codes=("unexpected_screen_go_back",),
        )
    if reason_code == "browser_session_crashed" and navigate_home_allowed:
        return RecoveryDecision(
            decision="navigate_home",
            safe_message=(
                "The browser view needs to be reopened, so I'll return to the product start."
            ),
            severity=severity,
            reason_codes=("browser_replacement_home_navigation",),
        )
    return RecoveryDecision(
        decision="ask_user",
        safe_message=(
            "I can't verify that step from the current screen. Would you like me to continue?"
        ),
        severity=severity,
        reason_codes=("needs_user_clarification",),
    )
