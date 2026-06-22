from live_demo_backend_common.observability import metric_names


def test_required_metric_names_exist() -> None:
    required = {
        metric_names.FIRST_AUDIO_LATENCY_SECONDS,
        metric_names.LLM_LATENCY_SECONDS,
        metric_names.STT_LATENCY_SECONDS,
        metric_names.TTS_FIRST_AUDIO_LATENCY_SECONDS,
        metric_names.BROWSER_ACTION_LATENCY_SECONDS,
        metric_names.POLICY_BLOCKS_TOTAL,
        metric_names.LATENCY_BUDGET_VIOLATIONS_TOTAL,
    }

    assert required <= metric_names.ALL_METRIC_NAMES


def test_session_id_is_not_allowed_metric_label() -> None:
    assert "session_id" not in metric_names.ALLOWED_LABEL_NAMES
    assert "trace_id" not in metric_names.ALLOWED_LABEL_NAMES
