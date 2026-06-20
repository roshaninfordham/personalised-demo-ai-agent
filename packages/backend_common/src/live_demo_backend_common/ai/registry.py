from __future__ import annotations

from live_demo_backend_common.ai.config import AiProviderSettings
from live_demo_backend_common.ai.embeddings.base import EmbeddingProvider
from live_demo_backend_common.ai.embeddings.disabled import DisabledEmbeddingProvider
from live_demo_backend_common.ai.embeddings.fake import FakeEmbeddingProvider
from live_demo_backend_common.ai.embeddings.nvidia_nim import NvidiaNimEmbeddingProvider
from live_demo_backend_common.ai.embeddings.ollama import OllamaEmbeddingProvider
from live_demo_backend_common.ai.embeddings.openai_compatible import (
    OpenAICompatibleEmbeddingProvider,
)
from live_demo_backend_common.ai.errors import ProviderConfigurationError
from live_demo_backend_common.ai.text.base import TextGenerationProvider
from live_demo_backend_common.ai.text.disabled import DisabledTextProvider
from live_demo_backend_common.ai.text.fake import FakeTextProvider
from live_demo_backend_common.ai.text.nvidia_nim import NvidiaNimTextProvider
from live_demo_backend_common.ai.text.ollama import OllamaTextProvider
from live_demo_backend_common.ai.text.openai_compatible import OpenAICompatibleTextProvider
from live_demo_backend_common.ai.types import ProviderHealth
from live_demo_backend_common.ai.vision.base import VisionUnderstandingProvider
from live_demo_backend_common.ai.vision.disabled import DisabledVisionProvider
from live_demo_backend_common.ai.vision.fake import FakeVisionProvider
from live_demo_backend_common.ai.vision.ollama import OllamaVisionProvider
from live_demo_backend_common.ai.vision.openai_compatible import (
    build_openai_compatible_vision_provider,
)


class ProviderRegistry:
    def __init__(self, settings: AiProviderSettings) -> None:
        self._settings = settings
        self._text_provider: TextGenerationProvider | None = None
        self._embedding_provider: EmbeddingProvider | None = None
        self._vision_provider: VisionUnderstandingProvider | None = None

    def get_text_provider(self) -> TextGenerationProvider:
        if self._text_provider is None:
            self._text_provider = self._build_text_provider()
        return self._text_provider

    def get_embedding_provider(self) -> EmbeddingProvider:
        if self._embedding_provider is None:
            self._embedding_provider = self._build_embedding_provider()
        return self._embedding_provider

    def get_vision_provider(self) -> VisionUnderstandingProvider:
        if self._vision_provider is None:
            self._vision_provider = self._build_vision_provider()
        return self._vision_provider

    async def health_check_all(self) -> dict[str, ProviderHealth]:
        text = await self.get_text_provider().health_check()
        embedding = await self.get_embedding_provider().health_check()
        vision = await self.get_vision_provider().health_check()
        return {"text": text, "embedding": embedding, "vision": vision}

    async def close(self) -> None:
        for provider in [self._text_provider, self._embedding_provider, self._vision_provider]:
            if provider is not None:
                await provider.close()

    def _build_text_provider(self) -> TextGenerationProvider:
        provider = self._settings.ai_text_provider
        if provider == "fake":
            return FakeTextProvider()
        if provider == "disabled":
            return DisabledTextProvider()
        if provider == "nvidia_nim":
            return NvidiaNimTextProvider(self._settings)
        if provider == "ollama":
            return OllamaTextProvider(self._settings)
        if provider in {"openai", "custom_openai_compatible"}:
            if not self._settings.ai_text_base_url:
                raise _configuration_error(provider, "text", "AI_TEXT_BASE_URL is required.")
            if not self._settings.ai_text_model:
                raise _configuration_error(provider, "text", "AI_TEXT_MODEL is required.")
            return OpenAICompatibleTextProvider(
                provider_name=provider,
                base_url=self._settings.ai_text_base_url,
                api_key=(
                    self._settings.ai_text_api_key.get_secret_value()
                    if self._settings.ai_text_api_key is not None
                    else None
                ),
                model_name=self._settings.ai_text_model,
                settings=self._settings,
                supports_streaming=self._settings.ai_text_enable_streaming,
                supports_tool_calling=self._settings.ai_text_enable_tool_calling,
                supports_json_schema=True,
            )
        raise _configuration_error(provider, "text", "Unsupported AI_TEXT_PROVIDER.")

    def _build_embedding_provider(self) -> EmbeddingProvider:
        provider = self._settings.ai_embedding_provider
        if provider == "fake":
            return FakeEmbeddingProvider(dimensions=self._settings.ai_embedding_dimensions)
        if provider == "disabled":
            return DisabledEmbeddingProvider()
        if provider == "nvidia_nim":
            return NvidiaNimEmbeddingProvider(self._settings)
        if provider == "ollama":
            return OllamaEmbeddingProvider(self._settings)
        if provider in {"openai", "custom_openai_compatible"}:
            if not self._settings.ai_embedding_base_url:
                raise _configuration_error(
                    provider,
                    "embedding",
                    "AI_EMBEDDING_BASE_URL is required.",
                )
            if not self._settings.ai_embedding_model:
                raise _configuration_error(
                    provider,
                    "embedding",
                    "AI_EMBEDDING_MODEL is required.",
                )
            return OpenAICompatibleEmbeddingProvider(
                provider_name=provider,
                base_url=self._settings.ai_embedding_base_url,
                api_key=(
                    self._settings.ai_embedding_api_key.get_secret_value()
                    if self._settings.ai_embedding_api_key is not None
                    else None
                ),
                model_name=self._settings.ai_embedding_model,
                dimensions=self._settings.ai_embedding_dimensions,
                settings=self._settings,
            )
        raise _configuration_error(provider, "embedding", "Unsupported AI_EMBEDDING_PROVIDER.")

    def _build_vision_provider(self) -> VisionUnderstandingProvider:
        provider = self._settings.ai_vision_provider
        if provider == "disabled":
            return DisabledVisionProvider()
        if provider == "fake":
            return FakeVisionProvider()
        if provider == "ollama":
            return OllamaVisionProvider(self._settings)
        if provider in {"nvidia_nim", "openai", "custom_openai_compatible"}:
            return build_openai_compatible_vision_provider(
                self._settings,
                provider_name=provider,
            )
        raise _configuration_error(provider, "vision", "Unsupported AI_VISION_PROVIDER.")


def _configuration_error(
    provider_name: str,
    provider_type: str,
    message: str,
) -> ProviderConfigurationError:
    return ProviderConfigurationError(
        provider_name=provider_name,
        model_name=None,
        operation=f"{provider_type}.configure",
        retryable=False,
        status_code=None,
        safe_message=message,
    )
