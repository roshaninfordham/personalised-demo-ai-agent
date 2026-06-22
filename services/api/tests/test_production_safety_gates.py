from typing import Any

import pytest
from pydantic import SecretStr

from live_demo_api.config import ApiSettings, validate_production_settings


def production_settings(**overrides: object) -> ApiSettings:
    values: dict[str, Any] = {
        "app_env": "production",
        "dev_allow_implicit_local_org": False,
        "allow_local_product_urls": False,
        "allow_destructive_actions": False,
        "cors_allowed_origins": "https://app.example.com",
        "ai_text_provider": "nvidia_nim",
        "jwt_secret": SecretStr("prod-jwt-secret"),
        "session_secret": SecretStr("prod-session-secret"),
        "redaction_hash_secret": SecretStr("prod-redaction-secret"),
        "crm_export_provider": "mock",
        "crm_export_dry_run": True,
    }
    values.update(overrides)
    return ApiSettings(**values)


def test_production_safety_gate_allows_hardened_configuration() -> None:
    validate_production_settings(production_settings())


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("dev_allow_implicit_local_org", True, "DEV_ALLOW_IMPLICIT_LOCAL_ORG"),
        ("allow_local_product_urls", True, "ALLOW_LOCAL_PRODUCT_URLS"),
        ("allow_destructive_actions", True, "ALLOW_DESTRUCTIVE_ACTIONS"),
        ("cors_allowed_origins", "*", "CORS_ALLOWED_ORIGINS=*"),
        ("ai_text_provider", "fake", "AI_TEXT_PROVIDER=fake"),
        ("jwt_secret", SecretStr(""), "JWT_SECRET"),
        ("session_secret", SecretStr("change_me"), "SESSION_SECRET"),
        ("redaction_hash_secret", SecretStr(""), "REDACTION_HASH_SECRET"),
    ],
)
def test_production_safety_gate_rejects_unsafe_configuration(
    field: str,
    value: object,
    expected: str,
) -> None:
    settings = production_settings(**{field: value})
    with pytest.raises(ValueError, match=expected):
        validate_production_settings(settings)
