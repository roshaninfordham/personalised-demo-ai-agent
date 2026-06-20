from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

import httpx

from live_demo_backend_common.ai.config import AiProviderSettings
from live_demo_backend_common.ai.embeddings.base import (
    EmbeddingCache,
    embedding_cache_key,
)
from live_demo_backend_common.ai.embeddings.vector_math import (
    l2_norm,
    normalize_l2,
    provider_validate_vector_dimensions,
)
from live_demo_backend_common.ai.errors import (
    ProviderConfigurationError,
    ProviderResponseValidationError,
    provider_error_from_http_status,
    provider_error_from_httpx_exception,
)
from live_demo_backend_common.ai.http_client import create_async_http_client
from live_demo_backend_common.ai.types import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingVector,
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
    TokenUsage,
)


class OpenAICompatibleEmbeddingProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        base_url: str,
        api_key: str | None,
        model_name: str,
        dimensions: int,
        settings: AiProviderSettings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.dimensions = dimensions
        self.settings = settings
        self.capabilities = frozenset({ProviderCapability.embeddings})
        self._client = client if client is not None else create_async_http_client(settings)
        self._owns_client = client is None
        self._cache = (
            EmbeddingCache(settings.ai_embedding_cache_max_items)
            if settings.ai_embedding_cache_enabled
            else None
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="embedding",
            model_name=self.model_name,
            status=ProviderStatus.healthy,
            capabilities=list(self.capabilities),
            checked_at=datetime.now(UTC),
            safe_message="Embedding provider is configured.",
        )

    async def embed_texts(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self._validate_request(request)
        started = time.monotonic()
        model_name = request.model or self.model_name
        cache_hits: dict[int, EmbeddingVector] = {}
        missing_texts: list[str] = []
        missing_indexes: list[int] = []
        if self._cache is not None:
            for index, text in enumerate(request.texts):
                key = embedding_cache_key(
                    provider_name=self.provider_name,
                    model_name=model_name,
                    dimensions=request.dimensions or self.dimensions,
                    normalize=request.normalize,
                    text=text,
                )
                cached = self._cache.get(key)
                if cached is None:
                    missing_indexes.append(index)
                    missing_texts.append(text)
                else:
                    cache_hits[index] = cached
        else:
            missing_indexes = list(range(len(request.texts)))
            missing_texts = list(request.texts)

        fetched = await self._fetch_embeddings(
            texts=missing_texts,
            model_name=model_name,
            dimensions=request.dimensions or self.dimensions,
            normalize=request.normalize,
            metadata=request.metadata,
        )
        vectors_by_index = dict(cache_hits)
        for original_index, vector in zip(missing_indexes, fetched, strict=True):
            rewritten = vector.model_copy(update={"text_index": original_index})
            vectors_by_index[original_index] = rewritten
            if self._cache is not None:
                self._cache.put(
                    embedding_cache_key(
                        provider_name=self.provider_name,
                        model_name=model_name,
                        dimensions=request.dimensions or self.dimensions,
                        normalize=request.normalize,
                        text=request.texts[original_index],
                    ),
                    rewritten,
                )
        return EmbeddingResponse(
            provider_name=self.provider_name,
            model_name=model_name,
            vectors=[vectors_by_index[index] for index in range(len(request.texts))],
            latency_ms=int((time.monotonic() - started) * 1000),
        )

    async def _fetch_embeddings(
        self,
        *,
        texts: list[str],
        model_name: str,
        dimensions: int,
        normalize: bool,
        metadata: dict[str, str],
    ) -> list[EmbeddingVector]:
        if not texts:
            return []
        try:
            response = await self._client.post(
                _join_api_path(self.base_url, "embeddings"),
                headers=self._headers(),
                json={"model": model_name, "input": texts},
                timeout=self.settings.ai_embedding_timeout_ms / 1000,
            )
        except httpx.HTTPError as exc:
            raise provider_error_from_httpx_exception(
                provider_name=self.provider_name,
                model_name=model_name,
                operation="embedding.embed_texts",
                exc=exc,
                trace_id=metadata.get("trace_id"),
            ) from exc
        if response.status_code >= 400:
            raise provider_error_from_http_status(
                provider_name=self.provider_name,
                model_name=model_name,
                operation="embedding.embed_texts",
                status_code=response.status_code,
                response_text=response.text,
                trace_id=metadata.get("trace_id"),
            )
        value = response.json()
        return self._parse_embeddings(
            value=value,
            model_name=model_name,
            dimensions=dimensions,
            normalize=normalize,
        )

    def _parse_embeddings(
        self,
        *,
        value: dict[str, Any],
        model_name: str,
        dimensions: int,
        normalize: bool,
    ) -> list[EmbeddingVector]:
        data = value.get("data")
        if not isinstance(data, list):
            raise ProviderResponseValidationError(
                provider_name=self.provider_name,
                model_name=model_name,
                operation="embedding.embed_texts",
                retryable=False,
                status_code=None,
                safe_message="Embedding response did not include data.",
            )
        vectors: list[EmbeddingVector] = []
        for item in sorted(
            data,
            key=lambda child: child.get("index", 0) if isinstance(child, dict) else 0,
        ):
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise ProviderResponseValidationError(
                    provider_name=self.provider_name,
                    model_name=model_name,
                    operation="embedding.embed_texts",
                    retryable=False,
                    status_code=None,
                    safe_message="Embedding response item was invalid.",
                )
            raw_vector = [float(value) for value in item["embedding"]]
            provider_validate_vector_dimensions(
                provider_name=self.provider_name,
                model_name=model_name,
                operation="embedding.embed_texts",
                vector=raw_vector,
                expected=dimensions,
            )
            final_vector = normalize_l2(raw_vector) if normalize else raw_vector
            vectors.append(
                EmbeddingVector(
                    text_index=int(item.get("index", len(vectors))),
                    vector=final_vector,
                    dimensions=dimensions,
                    l2_norm=l2_norm(final_vector),
                )
            )
        return vectors

    def _validate_request(self, request: EmbeddingRequest) -> None:
        if len(request.texts) > self.settings.ai_embedding_batch_size:
            raise ProviderConfigurationError(
                provider_name=self.provider_name,
                model_name=request.model or self.model_name,
                operation="embedding.embed_texts",
                retryable=False,
                status_code=None,
                safe_message="Embedding batch size exceeds configured limit.",
            )
        for text in request.texts:
            if len(text) > self.settings.ai_embedding_max_text_chars:
                raise ProviderConfigurationError(
                    provider_name=self.provider_name,
                    model_name=request.model or self.model_name,
                    operation="embedding.embed_texts",
                    retryable=False,
                    status_code=None,
                    safe_message="Embedding text exceeds configured length limit.",
                )
        if request.dimensions is not None and request.dimensions != self.dimensions:
            raise ProviderConfigurationError(
                provider_name=self.provider_name,
                model_name=request.model or self.model_name,
                operation="embedding.embed_texts",
                retryable=False,
                status_code=None,
                safe_message="Requested embedding dimensions do not match configured dimensions.",
            )

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers


def parse_embedding_usage(value: object) -> TokenUsage | None:
    if not isinstance(value, dict):
        return None
    return TokenUsage(
        prompt_tokens=(
            value.get("prompt_tokens") if isinstance(value.get("prompt_tokens"), int) else None
        ),
        total_tokens=value.get("total_tokens")
        if isinstance(value.get("total_tokens"), int)
        else None,
    )


def _join_api_path(base_url: str, suffix: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", suffix)
