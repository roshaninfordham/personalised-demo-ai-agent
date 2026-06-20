from live_demo_tts_service.health import get_health


def test_get_health() -> None:
    assert get_health()["status"] == "ok"
