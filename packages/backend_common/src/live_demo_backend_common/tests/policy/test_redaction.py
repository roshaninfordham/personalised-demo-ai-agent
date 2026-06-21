from __future__ import annotations

from live_demo_backend_common.policy.redaction import (
    RedactionConfig,
    RedactionContext,
    RedactionEngine,
    screenshot_metadata_redaction_metadata,
)


def test_text_redaction_patterns() -> None:
    engine = RedactionEngine(RedactionConfig(customer_name_list=("Acme Corp",)))
    email = engine.redact_text("alice@example.com", RedactionContext.PROMPT)
    assert email.redacted_value == "[REDACTED_EMAIL]"
    assert (
        engine.redact_text(
            "Bearer abcdefghijklmnopqrstuvwxyz123456",
            RedactionContext.LOG,
        ).redacted_value
        == "[REDACTED_BEARER_TOKEN]"
    )
    assert engine.redact_text("Acme Corp dashboard", RedactionContext.SCREEN_SUMMARY).applied


def test_json_sensitive_field_redaction() -> None:
    result = RedactionEngine().redact_json(
        {"safe": "value", "nested": {"password": "secret", "email": "user@example.com"}},
        RedactionContext.AUDIT,
    )
    assert result.redacted_value["nested"]["password"] == "[REDACTED_SECRET]"  # noqa: S105
    assert result.redacted_value["nested"]["email"] == "[REDACTED_EMAIL]"


def test_credit_card_luhn_and_screenshot_metadata_flag() -> None:
    result = RedactionEngine().redact_text("card 4242 4242 4242 4242", RedactionContext.LOG)
    assert result.redacted_value == "card [REDACTED_CREDIT_CARD]"
    metadata = screenshot_metadata_redaction_metadata(result)
    assert metadata["visual_redaction_applied"] is False
