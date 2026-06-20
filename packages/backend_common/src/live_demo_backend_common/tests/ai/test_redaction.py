from __future__ import annotations

from live_demo_backend_common.ai.redaction import redact_mapping, safe_hash_json, safe_hash_text


def test_redaction_and_hashing_are_deterministic() -> None:
    redacted = redact_mapping({"Authorization": "Bearer secret", "nested": {"api_key": "k"}})
    assert redacted["Authorization"] == "***REDACTED***"
    assert redacted["nested"] == {"api_key": "***REDACTED***"}
    assert safe_hash_text("abc") == safe_hash_text("abc")
    assert safe_hash_json({"b": 2, "a": 1}) == safe_hash_json({"a": 1, "b": 2})
