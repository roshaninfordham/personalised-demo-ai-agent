import pytest
from pydantic import SecretStr, ValidationError

from .helpers import test_settings


def test_default_providers_are_fake() -> None:
    settings = test_settings()
    assert settings.ai_stt_provider == "fake"
    assert settings.ai_tts_provider == "fake"


def test_invalid_stt_provider_rejected() -> None:
    with pytest.raises(ValidationError):
        test_settings(ai_stt_provider="bad")


def test_invalid_tts_provider_rejected() -> None:
    with pytest.raises(ValidationError):
        test_settings(ai_tts_provider="bad")


def test_safe_log_dict_redacts_secrets() -> None:
    settings = test_settings(ai_stt_api_key=SecretStr("secret-value"))
    logged = settings.safe_log_dict()
    assert logged["ai_stt_api_key"] == "***REDACTED***"
