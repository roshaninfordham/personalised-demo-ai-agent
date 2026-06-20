from live_demo_api.health import get_health


def test_get_health() -> None:
    assert get_health()["status"] == "ok"
