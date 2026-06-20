from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from live_demo_backend_common.ai.embeddings.vector_math import l2_norm, normalize_l2
from live_demo_backend_common.ai.types import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingVector,
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
)


class FakeEmbeddingProvider:
    provider_name = "fake"
    model_name = "fake-embedding-model"
    capabilities = frozenset({ProviderCapability.embeddings})

    def __init__(self, dimensions: int = 768) -> None:
        self.dimensions = dimensions

    async def close(self) -> None:
        return None

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="embedding",
            model_name=self.model_name,
            status=ProviderStatus.healthy,
            capabilities=list(self.capabilities),
            checked_at=datetime.now(UTC),
            safe_message="Fake embedding provider is healthy.",
        )

    async def embed_texts(self, request: EmbeddingRequest) -> EmbeddingResponse:
        dimensions = request.dimensions or self.dimensions
        vectors: list[EmbeddingVector] = []
        for text_index, text in enumerate(request.texts):
            raw = [_deterministic_hash_float(text, index) for index in range(dimensions)]
            final = normalize_l2(raw) if request.normalize else raw
            vectors.append(
                EmbeddingVector(
                    text_index=text_index,
                    vector=final,
                    dimensions=dimensions,
                    l2_norm=l2_norm(final),
                )
            )
        return EmbeddingResponse(
            provider_name=self.provider_name,
            model_name=request.model or self.model_name,
            vectors=vectors,
            latency_ms=0,
        )


def _deterministic_hash_float(text: str, index: int) -> float:
    digest = hashlib.sha256(f"{text}:{index}".encode()).digest()
    unsigned = int.from_bytes(digest[:8], "big") / 2**64
    return 2 * unsigned - 1
