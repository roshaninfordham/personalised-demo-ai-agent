from live_demo_api.agentic.turn_planner import AgenticPhase, plan_text_turn


def test_login_screen_turn_identifies_auth_gate_without_hallucinating() -> None:
    decision = plan_text_turn(
        "Can you show me the dashboard?",
        {
            "title": "Rebolt Generated App",
            "summary": "Main headings: Welcome back.",
            "auth_state": {"login_required": True},
        },
        [],
    )

    assert decision.phase == AgenticPhase.AUTH_HANDLING
    assert "cannot verify the authenticated app" in decision.response
    assert decision.action is None
    assert decision.blocked is False


def test_sign_up_tutorial_uses_visible_safe_action_only() -> None:
    action: dict[str, object] = {
        "action_id": "act_signup",
        "action_type": "click_element",
        "element_id": "el_signup",
        "label": "Sign up",
        "risk_level": "low",
    }

    decision = plan_text_turn(
        "Can you walk me through how to sign up?",
        {"auth_state": {"login_required": True}},
        [action],
    )

    assert decision.phase == AgenticPhase.AUTH_HANDLING
    assert decision.reason_code == "auth_signup_tutorial"
    assert decision.action == action
    assert "without submitting anything" in decision.response


def test_metric_action_ranking_prefers_high_success_low_latency_action() -> None:
    decision = plan_text_turn(
        "How do I create a metric?",
        {},
        [
            {
                "action_id": "act_new_metric_slow",
                "action_type": "click_element",
                "element_id": "el_new_metric",
                "label": "New Metric",
                "risk_level": "low",
                "score": 0.7,
                "success_rate": 0.4,
                "latency_cost": 0.9,
            },
            {
                "action_id": "act_create_metric",
                "action_type": "click_element",
                "element_id": "el_create_metric",
                "label": "Create Metric",
                "risk_level": "low",
                "score": 0.8,
                "success_rate": 0.95,
                "latency_cost": 0.1,
            },
        ],
    )

    assert decision.action is not None
    assert decision.action["action_id"] == "act_create_metric"


def test_action_ranking_penalizes_high_risk_candidates() -> None:
    decision = plan_text_turn(
        "Can you show reports?",
        {},
        [
            {
                "action_id": "act_export_reports",
                "action_type": "click_element",
                "element_id": "el_export_reports",
                "label": "Reports Export",
                "risk_level": "high",
                "score": 0.98,
            },
            {
                "action_id": "act_reports",
                "action_type": "click_element",
                "element_id": "el_reports",
                "label": "Reports",
                "risk_level": "low",
                "score": 0.72,
            },
        ],
    )

    assert decision.action is not None
    assert decision.action["action_id"] == "act_reports"


def test_auth_planner_does_not_click_sign_in_or_type_fields() -> None:
    actions: list[dict[str, object]] = [
        {
            "action_id": "act_signin",
            "action_type": "click_element",
            "element_id": "el_signin",
            "label": "Sign In",
            "risk_level": "medium",
        },
        {
            "action_id": "act_password",
            "action_type": "type_into_element",
            "element_id": "el_password",
            "label": "Password",
            "risk_level": "blocked",
        },
    ]

    decision = plan_text_turn(
        "Can you sign in?",
        {"auth_state": {"login_required": True}},
        actions,
    )

    assert decision.phase == AgenticPhase.AUTH_HANDLING
    assert decision.action is None


def test_unsupported_capability_question_uses_uncertainty() -> None:
    decision = plan_text_turn(
        "Does this integrate with Salesforce?",
        {"summary": "Main headings: Dashboard. Visible navigation: Reports."},
        [],
    )

    assert decision.phase == AgenticPhase.QUESTION_ANSWERING
    assert decision.reason_code == "unsupported_claim_avoided"
    assert "cannot verify" in decision.response
    assert "Salesforce integration exists" not in decision.response


def test_dangerous_request_is_blocked() -> None:
    decision = plan_text_turn("Can you delete this project?", {}, [])

    assert decision.blocked is True
    assert decision.reason_code == "dangerous_action_blocked"
    assert decision.action_type == "blocked_action"
