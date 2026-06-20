from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import httpx

from live_demo_backend_common.ai.config import AiProviderSettings
from live_demo_backend_common.ai.embeddings.vector_math import (
    l2_norm,
    normalize_l2,
    provider_validate_vector_dimensions,
)
from live_demo_backend_common.ai.errors import (
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
)


class OllamaEmbeddingProvider:
    provider_name = "ollama"
    capabilities = frozenset({ProviderCapability.embeddings})

    def __init__(
        self,
        settings: AiProviderSettings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model_name = settings.ollama_embedding_model
        self.dimensions = settings.ai_embedding_dimensions
        self._client = client if client is not None else create_async_http_client(settings)
        self._owns_client = client is None

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
            safe_message="Ollama embedding provider is configured.",
        )

    async def embed_texts(self, request: EmbeddingRequest) -> EmbeddingResponse:
        started = time.monotonic()
        endpoint = (
            "/api/embeddings"
            if self.settings.ollama_embedding_use_legacy_endpoint
            else "/api/embed"
        )
        body: dict[str, Any] = {
            "model": request.model or self.model_name,
            "input": request.texts,
            "truncate": True,
            "dimensions": request.dimensions or self.dimensions,
        }
        try:
            response = await self._client.post(
                f"{self.base_url}{endpoint}",
                json=body,
                timeout=self.settings.ai_embedding_timeout_ms / 1000,
            )
        except httpx.HTTPError as exc:
            raise provider_error_from_httpx_exception(
                provider_name=self.provider_name,
                model_name=request.model or self.model_name,
                operation="embedding.embed_texts",
                exc=exc,
                trace_id=request.metadata.get("trace_id"),
            ) from exc
        if response.status_code >= 400:
            raise provider_error_from_http_status(
                provider_name=self.provider_name,
                model_name=request.model or self.model_name,
                operation="embedding.embed_texts",
                status_code=response.status_code,
                response_text=response.text,
                trace_id=request.metadata.get("trace_id"),
            )
        payload = response.json()
        raw_embeddings = payload.get("embeddings")
        if raw_embeddings is None and isinstance(payload.get("embedding"), list):
            raw_embeddings = [payload["embedding"]]
        vectors: list[EmbeddingVector] = []
        expected_dimensions = request.dimensions or self.dimensions
        for index, raw in enumerate(raw_embeddings or []):
            raw_vector = [float(value) for value in raw]
            provider_validate_vector_dimensions(
                provider_name=self.provider_name,
                model_name=request.model or self.model_name,
                operation="embedding.embed_texts",
                vector=raw_vector,
                expected=expected_dimensions,
            )
            final_vector = normalize_l2(raw_vector) if request.normalize else raw_vector
            vectors.append(
                EmbeddingVector(
                    text_index=index,
                    vector=final_vector,
                    dimensions=expected_dimensions,
                    l2_norm=l2_norm(final_vector),
                )
            )
        return EmbeddingResponse(
            provider_name=self.provider_name,
            model_name=request.model or self.model_name,
            vectors=vectors,
            latency_ms=int((time.monotonic() - started) * 1000),
        )
