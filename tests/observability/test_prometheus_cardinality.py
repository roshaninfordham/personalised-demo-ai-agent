import pytest

from live_demo_backend_common.observability.metrics import (
    MetricCardinalityError,
    MetricRegistry,
    validate_metric_labels,
)


def test_uuid_label_rejected() -> None:
    with pytest.raises(MetricCardinalityError):
        validate_metric_labels(
            {"service": "api", "environment": "local", "route": "abc", "session_id": "x"}
        )


def test_email_label_value_rejected() -> None:
    with pytest.raises(MetricCardinalityError):
        validate_metric_labels(
            {"service": "api", "environment": "local", "provider": "user@example.com"}
        )


def test_url_label_value_rejected() -> None:
    with pytest.raises(MetricCardinalityError):
        validate_metric_labels(
            {"service": "api", "environment": "local", "route": "https://example.com/a"}
        )


def test_allowed_metric_observes_histogram() -> None:
    registry = MetricRegistry(service="api", environment="local")

    registry.observe(
        "live_demo_first_audio_latency_seconds",
        0.25,
        {"transport_provider": "small_webrtc"},
    )

    assert "live_demo_first_audio_latency_seconds" in registry.render_prometheus()
