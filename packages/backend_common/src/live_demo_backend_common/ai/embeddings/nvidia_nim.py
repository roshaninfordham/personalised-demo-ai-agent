from __future__ import annotations

import httpx

from live_demo_backend_common.ai.config import AiProviderSettings
from live_demo_backend_common.ai.embeddings.openai_compatible import (
    OpenAICompatibleEmbeddingProvider,
)
from live_demo_backend_common.ai.errors import ProviderConfigurationError


class NvidiaNimEmbeddingProvider(OpenAICompatibleEmbeddingProvider):
    def __init__(
        self,
        settings: AiProviderSettings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not settings.ai_embedding_base_url:
            raise ProviderConfigurationError(
                provider_name="nvidia_nim",
                model_name=settings.ai_embedding_model,
                operation="configure",
                retryable=False,
                status_code=None,
                safe_message="AI_EMBEDDING_BASE_URL is required for NVIDIA NIM embeddings.",
            )
        if not settings.ai_embedding_model:
            raise ProviderConfigurationError(
                provider_name="nvidia_nim",
                model_name=None,
                operation="configure",
                retryable=False,
                status_code=None,
                safe_message="AI_EMBEDDING_MODEL is required for NVIDIA NIM embeddings.",
            )
        super().__init__(
            provider_name="nvidia_nim",
            base_url=settings.ai_embedding_base_url,
            api_key=(
                settings.ai_embedding_api_key.get_secret_value()
                if settings.ai_embedding_api_key is not None
                else None
            ),
            model_name=settings.ai_embedding_model,
            dimensions=settings.ai_embedding_dimensions,
            settings=settings,
            client=client,
        )
