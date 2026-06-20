from __future__ import annotations

import pytest

from live_demo_backend_common.ai.errors import ProviderConfigurationError
from live_demo_backend_common.ai.registry import ProviderRegistry
from live_demo_backend_common.ai.text.fake import FakeTextProvider
from live_demo_backend_common.tests.ai.helpers import test_settings


def test_registry_returns_singletons_from_env_config() -> None:
    registry = ProviderRegistry(
        test_settings(
            ai_text_provider="fake",
            ai_embedding_provider="fake",
            ai_vision_provider="fake",
            ai_embedding_dimensions=4,
        )
    )
    assert isinstance(registry.get_text_provider(), FakeTextProvider)
    assert registry.get_text_provider() is registry.get_text_provider()
    assert registry.get_embedding_provider() is registry.get_embedding_provider()
    assert registry.get_vision_provider() is registry.get_vision_provider()


@pytest.mark.asyncio
async def test_registry_health_check_and_close() -> None:
    registry = ProviderRegistry(
        test_settings(
            ai_text_provider="fake",
            ai_embedding_provider="fake",
            ai_vision_provider="disabled",
        )
    )
    health = await registry.health_check_all()
    assert set(health) == {"text", "embedding", "vision"}
    await registry.close()


def test_registry_invalid_configuration_raises() -> None:
    registry = ProviderRegistry(
        test_settings(
            ai_text_provider="custom_openai_compatible",
            ai_text_base_url=None,
            ai_text_model="model",
        )
    )
    with pytest.raises(ProviderConfigurationError):
        registry.get_text_provider()


def test_production_rejects_fake_provider_by_default() -> None:
    with pytest.raises(ValueError):
        test_settings(app_env="production", ai_text_provider="fake")
