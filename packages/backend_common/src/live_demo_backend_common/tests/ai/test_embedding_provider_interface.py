from __future__ import annotations

import httpx
import pytest

from live_demo_backend_common.ai.embeddings.fake import FakeEmbeddingProvider
from live_demo_backend_common.ai.embeddings.nvidia_nim import NvidiaNimEmbeddingProvider
from live_demo_backend_common.ai.embeddings.ollama import OllamaEmbeddingProvider
from live_demo_backend_common.ai.embeddings.openai_compatible import (
    OpenAICompatibleEmbeddingProvider,
)
from live_demo_backend_common.ai.errors import ProviderResponseValidationError
from live_demo_backend_common.ai.types import EmbeddingRequest
from live_demo_backend_common.tests.ai.helpers import json_response, mock_client, test_settings


@pytest.mark.asyncio
async def test_fake_embedding_provider_is_deterministic() -> None:
    provider = FakeEmbeddingProvider(dimensions=8)
    first = await provider.embed_texts(EmbeddingRequest(texts=["alpha"], dimensions=8))
    second = await provider.embed_texts(EmbeddingRequest(texts=["alpha"], dimensions=8))
    assert first.vectors[0].vector == second.vectors[0].vector
    assert first.vectors[0].dimensions == 8


@pytest.mark.asyncio
async def test_openai_compatible_embeddings_parse_and_cache() -> None:
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        assert str(request.url) == "https://provider.test/v1/embeddings"
        return json_response(
            {
                "data": [
                    {"index": 0, "embedding": [1.0, 0.0, 0.0]},
                    {"index": 1, "embedding": [0.0, 1.0, 0.0]},
                ]
            }
        )

    provider = OpenAICompatibleEmbeddingProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key=None,
        model_name="embed",
        dimensions=3,
        settings=test_settings(ai_embedding_dimensions=3, ai_embedding_cache_enabled=True),
        client=mock_client(handler),
    )
    request = EmbeddingRequest(texts=["a", "b"], dimensions=3)
    first = await provider.embed_texts(request)
    second = await provider.embed_texts(request)
    assert len(first.vectors) == 2
    assert second.vectors[1].vector == [0.0, 1.0, 0.0]
    assert call_count == 1


@pytest.mark.asyncio
async def test_dimension_mismatch_raises_provider_validation_error() -> None:
    provider = OpenAICompatibleEmbeddingProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key=None,
        model_name="embed",
        dimensions=3,
        settings=test_settings(ai_embedding_dimensions=3),
        client=mock_client(
            lambda request: json_response({"data": [{"index": 0, "embedding": [1.0, 2.0]}]})
        ),
    )
    with pytest.raises(ProviderResponseValidationError):
        await provider.embed_texts(EmbeddingRequest(texts=["a"], dimensions=3))


@pytest.mark.asyncio
async def test_nim_embedding_reuses_compatible_adapter() -> None:
    provider = NvidiaNimEmbeddingProvider(
        test_settings(
            ai_embedding_provider="nvidia_nim",
            ai_embedding_base_url="https://integrate.api.nvidia.com/v1",
            ai_embedding_model="embed",
            ai_embedding_dimensions=2,
        ),
        client=mock_client(
            lambda request: json_response({"data": [{"index": 0, "embedding": [1.0, 0.0]}]})
        ),
    )
    response = await provider.embed_texts(EmbeddingRequest(texts=["a"], dimensions=2))
    assert response.provider_name == "nvidia_nim"


@pytest.mark.asyncio
async def test_ollama_embedding_uses_api_embed_by_default() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return json_response({"embeddings": [[1.0, 0.0]]})

    provider = OllamaEmbeddingProvider(
        test_settings(
            ollama_base_url="http://ollama:11434",
            ollama_embedding_model="nomic",
            ai_embedding_dimensions=2,
        ),
        client=mock_client(handler),
    )
    response = await provider.embed_texts(EmbeddingRequest(texts=["a"], dimensions=2))
    assert captured["url"] == "http://ollama:11434/api/embed"
    assert response.vectors[0].dimensions == 2
