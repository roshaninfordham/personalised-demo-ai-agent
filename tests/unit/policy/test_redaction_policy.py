from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine


def test_redaction_policy_masks_prompt_and_json_secrets() -> None:
    engine = RedactionEngine()

    text = engine.redact_text(
        "Contact alice@example.com with Bearer abcdefghijklmnop1234",
        RedactionContext.PROMPT,
    )
    payload = engine.redact_json(
        {"authorization": "Bearer abcdefghijklmnop1234", "note": "safe"},
        RedactionContext.LOG,
    )

    assert text.redacted_value == "Contact [REDACTED_EMAIL] with [REDACTED_BEARER_TOKEN]"
    assert payload.redacted_value == {"authorization": "[REDACTED_SECRET]", "note": "safe"}
