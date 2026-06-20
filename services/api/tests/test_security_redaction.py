from live_demo_api.logging_config import redact_mapping, redact_value


def test_redact_value_hides_known_secret_keys() -> None:
    assert redact_value("authorization", "Bearer token") == "***REDACTED***"
    assert redact_value("object_storage_secret_key", "secret") == "***REDACTED***"
    assert redact_value("plain", "value") == "value"


def test_redact_mapping_hides_nested_secret_keys() -> None:
    redacted = redact_mapping({"api_key": "abc", "nested": {"refresh_token": "def"}})
    assert redacted["api_key"] == "***REDACTED***"
    assert redacted["nested"] == {"refresh_token": "***REDACTED***"}
