from __future__ import annotations

import json
import time

import httpx
from pydantic import ValidationError

from live_demo_backend_common.ai.config import AiProviderSettings
from live_demo_backend_common.ai.errors import (
    ProviderCapabilityError,
    ProviderConfigurationError,
    ProviderResponseValidationError,
)
from live_demo_backend_common.ai.text.openai_compatible import OpenAICompatibleTextProvider
from live_demo_backend_common.ai.types import (
    ChatMessage,
    MessageRole,
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
    TextGenerationRequest,
    UiVisionExtractionRequest,
    UiVisionExtractionResponse,
    VisionDescriptionRequest,
    VisionDescriptionResponse,
)
from live_demo_backend_common.ai.vision.base import image_data_uri


class OpenAICompatibleVisionProvider:
    provider_name: str
    model_name: str | None

    def __init__(
        self,
        *,
        provider_name: str,
        base_url: str,
        api_key: str | None,
        model_name: str,
        settings: AiProviderSettings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self.settings = settings
        self._text_provider = OpenAICompatibleTextProvider(
            provider_name=provider_name,
            base_url=base_url,
            api_key=api_key,
            model_name=model_name,
            settings=settings,
            supports_streaming=False,
            supports_tool_calling=False,
            supports_json_schema=True,
            client=client,
        )

    async def close(self) -> None:
        await self._text_provider.close()

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="vision",
            model_name=self.model_name,
            status=ProviderStatus.healthy,
            capabilities=[ProviderCapability.vision],
            safe_message="Vision provider is configured.",
        )

    async def describe_image(
        self,
        request: VisionDescriptionRequest,
    ) -> VisionDescriptionResponse:
        started = time.monotonic()
        data_uri = image_data_uri(
            request.image,
            provider_name=self.provider_name,
            model_name=self.model_name,
            max_size_bytes=self.settings.ai_vision_max_image_size_bytes,
        )
        response = await self._text_provider.generate(
            TextGenerationRequest(
                messages=[
                    ChatMessage(
                        role=MessageRole.user,
                        content=json.dumps(
                            {
                                "type": "multimodal_prompt",
                                "prompt": request.prompt,
                                "image_url": data_uri,
                            },
                            sort_keys=True,
                        ),
                    )
                ],
                max_output_tokens=request.max_output_tokens,
                metadata=request.metadata,
            )
        )
        return VisionDescriptionResponse(
            provider_name=self.provider_name,
            model_name=self.model_name,
            description=response.content,
            latency_ms=int((time.monotonic() - started) * 1000),
        )

    async def extract_ui_facts(
        self,
        request: UiVisionExtractionRequest,
    ) -> UiVisionExtractionResponse:
        if self.settings.ai_vision_allow_json_schema_downgrade:
            response_format = "json_object"
            json_schema = None
        elif ProviderCapability.json_schema_output in self._text_provider.capabilities:
            response_format = "json_schema"
            json_schema = UiVisionExtractionResponse.model_json_schema()
        else:
            raise ProviderCapabilityError(
                provider_name=self.provider_name,
                model_name=self.model_name,
                operation="vision.extract_ui_facts",
                retryable=False,
                status_code=None,
                safe_message="Vision provider does not support structured UI extraction.",
            )
        description = await self.describe_image(
            VisionDescriptionRequest(
                image=request.image,
                prompt=request.prompt,
                max_output_tokens=request.max_output_tokens,
                metadata={**request.metadata, "response_format": response_format},
            )
        )
        try:
            payload = json.loads(description.description)
            if json_schema is not None:
                payload.setdefault("provider_name", self.provider_name)
                payload.setdefault("model_name", self.model_name)
                payload.setdefault("latency_ms", description.latency_ms)
            return UiVisionExtractionResponse.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ProviderResponseValidationError(
                provider_name=self.provider_name,
                model_name=self.model_name,
                operation="vision.extract_ui_facts",
                retryable=False,
                status_code=None,
                safe_message="Vision provider returned invalid UI extraction JSON.",
                internal_message=str(exc),
            ) from exc


def build_openai_compatible_vision_provider(
    settings: AiProviderSettings,
    *,
    provider_name: str,
    client: httpx.AsyncClient | None = None,
) -> OpenAICompatibleVisionProvider:
    if not settings.ai_vision_base_url:
        raise ProviderConfigurationError(
            provider_name=provider_name,
            model_name=settings.ai_vision_model,
            operation="configure",
            retryable=False,
            status_code=None,
            safe_message="AI_VISION_BASE_URL is required for vision provider.",
        )
    if not settings.ai_vision_model:
        raise ProviderConfigurationError(
            provider_name=provider_name,
            model_name=None,
            operation="configure",
            retryable=False,
            status_code=None,
            safe_message="AI_VISION_MODEL is required for vision provider.",
        )
    return OpenAICompatibleVisionProvider(
        provider_name=provider_name,
        base_url=settings.ai_vision_base_url,
        api_key=(
            settings.ai_vision_api_key.get_secret_value()
            if settings.ai_vision_api_key is not None
            else None
        ),
        model_name=settings.ai_vision_model,
        settings=settings,
        client=client,
    )
