from live_demo_api.orchestration.readiness import compute_readiness, readiness_allows_start


def test_readiness_score_formula_correct() -> None:
    readiness = compute_readiness(
        browser_session_ready=True,
        url_loaded=True,
        first_screen_read=True,
        safe_action_count=2,
        voice_session_ready=True,
        join_config_ready=True,
        recipe_compiled=False,
        learner_enqueued=True,
        provider_warmed_count=2,
        provider_required_count=3,
    )

    assert readiness.score == 0.9
    assert readiness.safe_actions_available == 2 / 3
    assert readiness.providers_warmed == 2 / 3


def test_required_browser_failure_prevents_ready() -> None:
    readiness = compute_readiness(
        browser_session_ready=False,
        url_loaded=False,
        first_screen_read=False,
        safe_action_count=0,
        voice_session_ready=True,
        join_config_ready=True,
        recipe_compiled=True,
        learner_enqueued=True,
        provider_warmed_count=3,
    )

    allowed, runtime_state = readiness_allows_start(readiness)

    assert allowed is False
    assert runtime_state == "browser_required_not_ready"
