from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator

import httpx

from live_demo_backend_common.ai.config import AiProviderSettings
from live_demo_backend_common.ai.errors import (
    ProviderCapabilityError,
    ProviderConfigurationError,
    ProviderResponseValidationError,
    provider_error_from_http_status,
    provider_error_from_httpx_exception,
)
from live_demo_backend_common.ai.http_client import create_async_http_client
from live_demo_backend_common.ai.text.openai_compatible import OpenAICompatibleTextProvider
from live_demo_backend_common.ai.types import (
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
    TextGenerationChunk,
    TextGenerationFinishReason,
    TextGenerationRequest,
    TextGenerationResponse,
)


class OllamaTextProvider:
    provider_name = "ollama"

    def __init__(
        self,
        settings: AiProviderSettings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.model_name = settings.ollama_text_model or settings.ai_text_model or ""
        if not self.model_name:
            raise ProviderConfigurationError(
                provider_name=self.provider_name,
                model_name=None,
                operation="configure",
                retryable=False,
                status_code=None,
                safe_message="OLLAMA_TEXT_MODEL or AI_TEXT_MODEL is required for Ollama text.",
            )
        self.mode = settings.ollama_text_mode
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.capabilities = frozenset(
            {ProviderCapability.text_generate, ProviderCapability.text_stream}
        )
        self._client = client if client is not None else create_async_http_client(settings)
        self._owns_client = client is None
        self._compatible: OpenAICompatibleTextProvider | None = None
        if self.mode == "openai_compatible":
            self._compatible = OpenAICompatibleTextProvider(
                provider_name="ollama",
                base_url=f"{self.base_url}/v1",
                api_key="ollama",
                model_name=self.model_name,
                settings=settings,
                supports_streaming=settings.ai_text_enable_streaming,
                supports_tool_calling=False,
                supports_json_schema=False,
                client=self._client,
            )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def health_check(self) -> ProviderHealth:
        started = time.monotonic()
        try:
            response = await self._client.get(
                f"{self.base_url}/api/version",
                timeout=self.settings.ollama_timeout_ms / 1000,
            )
            status = (
                ProviderStatus.healthy if response.status_code < 400 else ProviderStatus.degraded
            )
        except httpx.HTTPError:
            status = ProviderStatus.degraded
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="text",
            model_name=self.model_name,
            status=status,
            latency_ms=int((time.monotonic() - started) * 1000),
            capabilities=list(self.capabilities),
            safe_message="Ollama health check completed.",
        )

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResponse:
        if self._compatible is not None:
            return await self._compatible.generate(request)
        started = time.monotonic()
        try:
            response = await self._client.post(
                f"{self.base_url}/api/chat",
                json=self._native_body(request, stream=False),
                timeout=(request.timeout_ms or self.settings.ollama_timeout_ms) / 1000,
            )
        except httpx.HTTPError as exc:
            raise provider_error_from_httpx_exception(
                provider_name=self.provider_name,
                model_name=self.model_name,
                operation="text.generate",
                exc=exc,
                trace_id=request.metadata.get("trace_id"),
            ) from exc
        if response.status_code >= 400:
            raise provider_error_from_http_status(
                provider_name=self.provider_name,
                model_name=self.model_name,
                operation="text.generate",
                status_code=response.status_code,
                response_text=response.text,
                trace_id=request.metadata.get("trace_id"),
            )
        data = response.json()
        message = data.get("message")
        if not isinstance(message, dict):
            raise ProviderResponseValidationError(
                provider_name=self.provider_name,
                model_name=self.model_name,
                operation="text.generate",
                retryable=False,
                status_code=None,
                safe_message="Ollama response did not include a message.",
            )
        return TextGenerationResponse(
            provider_name=self.provider_name,
            model_name=request.model or self.model_name,
            content=str(message.get("content") or ""),
            finish_reason=TextGenerationFinishReason.stop,
            latency_ms=int((time.monotonic() - started) * 1000),
            request_id=request.metadata.get("request_id"),
        )

    async def stream(self, request: TextGenerationRequest) -> AsyncIterator[TextGenerationChunk]:
        if self._compatible is not None:
            async for chunk in self._compatible.stream(request):
                yield chunk
            return
        started = time.monotonic()
        first_token_latency_ms: int | None = None
        try:
            async with self._client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=self._native_body(request, stream=True),
                timeout=(request.timeout_ms or self.settings.ollama_timeout_ms) / 1000,
            ) as response:
                if response.status_code >= 400:
                    text = await response.aread()
                    raise provider_error_from_http_status(
                        provider_name=self.provider_name,
                        model_name=self.model_name,
                        operation="text.stream",
                        status_code=response.status_code,
                        response_text=text.decode("utf-8", errors="replace"),
                        trace_id=request.metadata.get("trace_id"),
                    )
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    payload = json.loads(line)
                    message = payload.get("message") or {}
                    delta = str(message.get("content") or "") if isinstance(message, dict) else ""
                    if first_token_latency_ms is None and delta:
                        first_token_latency_ms = int((time.monotonic() - started) * 1000)
                    done = bool(payload.get("done"))
                    yield TextGenerationChunk(
                        provider_name=self.provider_name,
                        model_name=request.model or self.model_name,
                        delta_text=delta,
                        is_final=done,
                        finish_reason=(TextGenerationFinishReason.stop if done else None),
                        latency_ms=int((time.monotonic() - started) * 1000),
                        first_token_latency_ms=first_token_latency_ms,
                        request_id=request.metadata.get("request_id"),
                    )
                    if done:
                        return
        except httpx.HTTPError as exc:
            raise provider_error_from_httpx_exception(
                provider_name=self.provider_name,
                model_name=self.model_name,
                operation="text.stream",
                exc=exc,
                trace_id=request.metadata.get("trace_id"),
            ) from exc

    async def tool_call(self, request: TextGenerationRequest) -> TextGenerationResponse:
        raise ProviderCapabilityError(
            provider_name=self.provider_name,
            model_name=request.model or self.model_name,
            operation="text.tool_call",
            retryable=False,
            status_code=None,
            safe_message="Ollama native tool calling is not implemented in Phase 4.",
        )

    def _native_body(self, request: TextGenerationRequest, *, stream: bool) -> dict[str, object]:
        return {
            "model": request.model or self.model_name,
            "messages": [
                {"role": message.role.value, "content": message.content}
                for message in request.messages
            ],
            "stream": stream,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
                "num_predict": request.max_output_tokens,
            },
            "keep_alive": self.settings.ollama_keep_alive,
        }
