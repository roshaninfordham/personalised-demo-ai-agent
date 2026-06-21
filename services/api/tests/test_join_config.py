from live_demo_api.orchestration.join_config import sanitize_join_config


def test_join_config_sanitizer_removes_secret_like_fields() -> None:
    sanitized = sanitize_join_config(
        {
            "session_id": "session",
            "join": {"signaling_url": "wss://example.test", "api_key": "secret"},
            "provider_api_key": "secret",
            "token": "secret",
            "capabilities": {"audio": True},
        }
    )

    assert "provider_api_key" not in sanitized
    assert "token" not in sanitized
    assert sanitized["join"] == {"signaling_url": "wss://example.test"}
    assert sanitized["capabilities"] == {"audio": True}
