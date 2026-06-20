from __future__ import annotations

from datetime import UTC, datetime

from live_demo_backend_common.ai.errors import ProviderCapabilityError
from live_demo_backend_common.ai.types import (
    EmbeddingRequest,
    EmbeddingResponse,
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
)


class DisabledEmbeddingProvider:
    provider_name = "disabled"
    model_name = "disabled"
    dimensions = 0
    capabilities: frozenset[ProviderCapability] = frozenset()

    async def close(self) -> None:
        return None

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="embedding",
            model_name=None,
            status=ProviderStatus.disabled,
            checked_at=datetime.now(UTC),
            safe_message="Embedding provider is disabled.",
        )

    async def embed_texts(self, request: EmbeddingRequest) -> EmbeddingResponse:
        raise ProviderCapabilityError(
            provider_name=self.provider_name,
            model_name=None,
            operation="embedding.embed_texts",
            retryable=False,
            status_code=None,
            safe_message="Embedding provider is disabled.",
        )
