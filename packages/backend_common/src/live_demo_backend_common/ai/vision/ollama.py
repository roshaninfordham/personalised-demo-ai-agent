from __future__ import annotations

import base64
import time

import httpx

from live_demo_backend_common.ai.config import AiProviderSettings
from live_demo_backend_common.ai.errors import ProviderConfigurationError
from live_demo_backend_common.ai.http_client import create_async_http_client
from live_demo_backend_common.ai.types import (
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
    UiVisionExtractionRequest,
    UiVisionExtractionResponse,
    VisionDescriptionRequest,
    VisionDescriptionResponse,
)
from live_demo_backend_common.ai.vision.base import image_bytes_from_input


class OllamaVisionProvider:
    provider_name = "ollama"
    model_name: str | None
    capabilities = frozenset({ProviderCapability.vision})

    def __init__(
        self,
        settings: AiProviderSettings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        if not settings.ai_vision_model:
            raise ProviderConfigurationError(
                provider_name=self.provider_name,
                model_name=None,
                operation="configure",
                retryable=False,
                status_code=None,
                safe_message="AI_VISION_MODEL is required for Ollama vision.",
            )
        self.settings = settings
        self.model_name = settings.ai_vision_model
        self.base_url = settings.ollama_base_url.rstrip("/")
        self._client = client if client is not None else create_async_http_client(settings)
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="vision",
            model_name=self.model_name,
            status=ProviderStatus.healthy,
            capabilities=list(self.capabilities),
            safe_message="Ollama vision provider is configured.",
        )

    async def describe_image(
        self,
        request: VisionDescriptionRequest,
    ) -> VisionDescriptionResponse:
        started = time.monotonic()
        payload = image_bytes_from_input(
            request.image,
            provider_name=self.provider_name,
            model_name=self.model_name,
            max_size_bytes=self.settings.ai_vision_max_image_size_bytes,
        )
        response = await self._client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": request.prompt,
                        "images": [base64.b64encode(payload).decode("ascii")],
                    }
                ],
                "stream": False,
            },
            timeout=self.settings.ai_vision_timeout_ms / 1000,
        )
        response.raise_for_status()
        data = response.json()
        message = data.get("message") or {}
        description = str(message.get("content") or "") if isinstance(message, dict) else ""
        return VisionDescriptionResponse(
            provider_name=self.provider_name,
            model_name=self.model_name,
            description=description,
            latency_ms=int((time.monotonic() - started) * 1000),
        )

    async def extract_ui_facts(
        self,
        request: UiVisionExtractionRequest,
    ) -> UiVisionExtractionResponse:
        description = await self.describe_image(
            VisionDescriptionRequest(
                image=request.image,
                prompt=request.prompt,
                max_output_tokens=request.max_output_tokens,
                metadata=request.metadata,
            )
        )
        return UiVisionExtractionResponse(
            provider_name=self.provider_name,
            model_name=self.model_name,
            facts=[],
            summary=description.description,
            latency_ms=description.latency_ms,
        )
