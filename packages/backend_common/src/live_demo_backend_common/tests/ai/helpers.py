from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx

from live_demo_backend_common.ai.config import AiProviderSettings


def test_settings(**overrides: Any) -> AiProviderSettings:
    defaults: dict[str, Any] = {
        "ai_text_provider": "fake",
        "ai_text_model": "test-text",
        "ai_text_base_url": "https://provider.test/v1",
        "ai_embedding_provider": "fake",
        "ai_embedding_model": "test-embedding",
        "ai_embedding_base_url": "https://provider.test/v1",
        "ai_vision_provider": "disabled",
        "ai_vision_model": "test-vision",
        "ai_vision_base_url": "https://provider.test/v1",
        "ollama_text_model": "llama-test",
        "app_env": "local",
    }
    defaults.update(overrides)
    return AiProviderSettings(**defaults)


def mock_client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def json_response(data: dict[str, Any], status_code: int = 200) -> httpx.Response:
    return httpx.Response(status_code=status_code, json=data)
