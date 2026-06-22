from live_demo_agent_runtime.auth.login_screen_detector import detect_login_screen


def test_detects_login_screen_from_password_and_sign_in_elements() -> None:
    detection = detect_login_screen(
        {
            "url": "https://app.example.com/signin",
            "title": "Rebolt Generated App",
            "visible_text": "Email Password Sign In Sign up",
            "elements": [
                {"role": "textbox", "label": "Email", "input_type": "email"},
                {"role": "textbox", "label": "Password", "input_type": "password"},
                {"role": "button", "label": "Sign In"},
                {"role": "link", "label": "Sign up"},
            ],
        }
    )

    assert detection.login_required is True
    assert detection.confidence >= 0.8
    assert "password" in detection.detected_fields
    assert "sign_in" in detection.detected_actions
    assert "open_sign_up_with_confirmation" in detection.safe_options


def test_does_not_classify_dashboard_as_login_screen() -> None:
    detection = detect_login_screen(
        {
            "url": "https://app.example.com/dashboard",
            "title": "Dashboard",
            "visible_text": "Revenue Metrics Reports Add Metric",
            "elements": [{"role": "button", "label": "Add Metric"}],
        }
    )

    assert detection.login_required is False
    assert "password" not in detection.detected_fields
