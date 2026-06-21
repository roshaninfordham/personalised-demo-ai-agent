from live_demo_api.orchestration.orchestration_recovery import (
    classify_recovery_reason,
    decide_recovery_action,
)


def test_stale_element_recovery_reads_current_screen() -> None:
    decision = decide_recovery_action(
        reason_code="stale_element",
        attempt_count=1,
        max_attempts=2,
        screen_available=True,
        go_back_allowed=True,
        navigate_home_allowed=True,
    )

    assert decision.decision == "read_current_screen"
    assert decision.severity == "low"


def test_unexpected_screen_tries_go_back_when_allowed() -> None:
    decision = decide_recovery_action(
        reason_code="unexpected_screen",
        attempt_count=1,
        max_attempts=2,
        screen_available=True,
        go_back_allowed=True,
        navigate_home_allowed=True,
    )

    assert decision.decision == "go_back"


def test_max_attempts_enters_degraded_mode() -> None:
    decision = decide_recovery_action(
        reason_code="browser_session_crashed",
        attempt_count=3,
        max_attempts=2,
        screen_available=False,
        go_back_allowed=True,
        navigate_home_allowed=True,
    )

    assert decision.decision == "enter_degraded_mode"
    assert "recovery_attempts_exceeded" in decision.reason_codes


def test_recovery_reason_classification_is_deterministic() -> None:
    assert classify_recovery_reason("high_risk_screen") == "high"
    assert classify_recovery_reason("stale_element") == "low"
    assert classify_recovery_reason("unknown_reason") == "medium"
