from __future__ import annotations

import httpx

from live_demo_backend_common.ai.config import AiProviderSettings
from live_demo_backend_common.ai.errors import ProviderConfigurationError
from live_demo_backend_common.ai.text.openai_compatible import OpenAICompatibleTextProvider


class NvidiaNimTextProvider(OpenAICompatibleTextProvider):
    def __init__(
        self,
        settings: AiProviderSettings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not settings.ai_text_base_url:
            raise ProviderConfigurationError(
                provider_name="nvidia_nim",
                model_name=settings.ai_text_model,
                operation="configure",
                retryable=False,
                status_code=None,
                safe_message="AI_TEXT_BASE_URL is required for NVIDIA NIM.",
            )
        if not settings.ai_text_model:
            raise ProviderConfigurationError(
                provider_name="nvidia_nim",
                model_name=None,
                operation="configure",
                retryable=False,
                status_code=None,
                safe_message="AI_TEXT_MODEL is required for NVIDIA NIM.",
            )
        super().__init__(
            provider_name="nvidia_nim",
            base_url=settings.ai_text_base_url,
            api_key=(
                settings.ai_text_api_key.get_secret_value()
                if settings.ai_text_api_key is not None
                else None
            ),
            model_name=settings.ai_text_model,
            settings=settings,
            supports_streaming=settings.ai_text_enable_streaming,
            supports_tool_calling=settings.ai_text_enable_tool_calling,
            supports_json_schema=True,
            client=client,
        )
