from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urljoin

import httpx

from live_demo_backend_common.ai.circuit_breaker import CircuitBreaker
from live_demo_backend_common.ai.config import AiProviderSettings
from live_demo_backend_common.ai.errors import (
    ProviderBadRequestError,
    ProviderCapabilityError,
    ProviderResponseValidationError,
    ProviderStreamingError,
    provider_error_from_http_status,
    provider_error_from_httpx_exception,
)
from live_demo_backend_common.ai.http_client import create_async_http_client
from live_demo_backend_common.ai.redaction import safe_hash_json
from live_demo_backend_common.ai.retry import RetryPolicy, retry_async
from live_demo_backend_common.ai.types import (
    ChatMessage,
    MessageRole,
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
    TextGenerationChunk,
    TextGenerationFinishReason,
    TextGenerationRequest,
    TextGenerationResponse,
    TokenUsage,
    ToolCall,
)


class OpenAICompatibleTextProvider:
    def __init__(
        self,
        *,
        provider_name: str,
        base_url: str,
        api_key: str | None,
        model_name: str,
        settings: AiProviderSettings,
        supports_streaming: bool = True,
        supports_tool_calling: bool = True,
        supports_json_schema: bool = False,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.settings = settings
        capabilities = {ProviderCapability.text_generate}
        if supports_streaming:
            capabilities.add(ProviderCapability.text_stream)
        if supports_tool_calling:
            capabilities.add(ProviderCapability.tool_calling)
        if supports_json_schema:
            capabilities.add(ProviderCapability.json_schema_output)
        self.capabilities = frozenset(capabilities)
        self._client = client if client is not None else create_async_http_client(settings)
        self._owns_client = client is None
        self._circuit = CircuitBreaker(
            provider_name=provider_name,
            failure_threshold=settings.ai_provider_circuit_failure_threshold,
            cooldown_seconds=settings.ai_provider_circuit_cooldown_seconds,
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def health_check(self) -> ProviderHealth:
        started = time.monotonic()
        mode = self.settings.ai_text_healthcheck_mode
        if mode == "disabled":
            return ProviderHealth(
                provider_name=self.provider_name,
                provider_type="text",
                model_name=self.model_name,
                status=ProviderStatus.disabled,
                capabilities=list(self.capabilities),
                checked_at=_now(),
                safe_message="Text provider health check is disabled.",
            )
        try:
            if mode == "chat":
                await self.generate(
                    TextGenerationRequest(
                        messages=[ChatMessage(role=MessageRole.user, content="ping")],
                        max_output_tokens=1,
                        timeout_ms=self.settings.ai_text_timeout_ms,
                    )
                )
            else:
                response = await self._client.get(
                    self._models_url(),
                    headers=self._headers(None),
                    timeout=self.settings.ai_text_timeout_ms / 1000,
                )
                if response.status_code >= 400:
                    raise provider_error_from_http_status(
                        provider_name=self.provider_name,
                        model_name=self.model_name,
                        operation="health_check",
                        status_code=response.status_code,
                        response_text=response.text,
                    )
            status = ProviderStatus.healthy
            message = "Provider is reachable."
        except Exception:
            status = ProviderStatus.degraded
            message = "Provider health check failed safely."
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="text",
            model_name=self.model_name,
            status=status,
            latency_ms=_elapsed_ms(started),
            capabilities=list(self.capabilities),
            checked_at=_now(),
            safe_message=message,
        )

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResponse:
        started = time.monotonic()
        operation = "text.generate"
        self._circuit.before_request(model_name=self._model_for(request), operation=operation)

        async def do_request() -> httpx.Response:
            body = self._build_chat_body(request, stream=False)
            try:
                response = await self._client.post(
                    self._chat_url(),
                    headers=self._headers(request),
                    json=body,
                    timeout=(request.timeout_ms or self.settings.ai_text_timeout_ms) / 1000,
                )
            except httpx.HTTPError as exc:
                raise provider_error_from_httpx_exception(
                    provider_name=self.provider_name,
                    model_name=self._model_for(request),
                    operation=operation,
                    exc=exc,
                    trace_id=request.metadata.get("trace_id"),
                ) from exc
            if response.status_code >= 400:
                raise provider_error_from_http_status(
                    provider_name=self.provider_name,
                    model_name=self._model_for(request),
                    operation=operation,
                    status_code=response.status_code,
                    response_text=response.text,
                    trace_id=request.metadata.get("trace_id"),
                )
            return response

        try:
            response = await retry_async(
                do_request,
                RetryPolicy(
                    max_retries=self.settings.ai_provider_hot_path_max_retries,
                    base_delay_ms=self.settings.ai_provider_retry_base_delay_ms,
                    max_delay_ms=self.settings.ai_provider_retry_max_delay_ms,
                ),
            )
            parsed = response.json()
            result = self._parse_chat_response(
                parsed,
                request=request,
                started=started,
                first_token_latency_ms=None,
            )
            self._circuit.record_success()
            return result
        except Exception as exc:
            retryable = getattr(exc, "retryable", False)
            self._circuit.record_failure(retryable=bool(retryable))
            raise

    async def stream(self, request: TextGenerationRequest) -> AsyncIterator[TextGenerationChunk]:
        if ProviderCapability.text_stream not in self.capabilities:
            raise ProviderCapabilityError(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                operation="text.stream",
                retryable=False,
                status_code=None,
                safe_message="Text provider does not support streaming.",
            )
        started = time.monotonic()
        first_token_latency_ms: int | None = None
        emitted_any = False
        self._circuit.before_request(model_name=self._model_for(request), operation="text.stream")
        try:
            async with self._client.stream(
                "POST",
                self._chat_url(),
                headers=self._headers(request),
                json=self._build_chat_body(request, stream=True),
                timeout=(request.timeout_ms or self.settings.ai_text_timeout_ms) / 1000,
            ) as response:
                if response.status_code >= 400:
                    text = await response.aread()
                    raise provider_error_from_http_status(
                        provider_name=self.provider_name,
                        model_name=self._model_for(request),
                        operation="text.stream",
                        status_code=response.status_code,
                        response_text=text.decode("utf-8", errors="replace"),
                        trace_id=request.metadata.get("trace_id"),
                    )
                async for event_payload in iter_sse_data_lines(response.aiter_lines()):
                    if event_payload == "[DONE]":
                        yield TextGenerationChunk(
                            provider_name=self.provider_name,
                            model_name=self._model_for(request),
                            is_final=True,
                            finish_reason=TextGenerationFinishReason.stop,
                            latency_ms=_elapsed_ms(started),
                            first_token_latency_ms=first_token_latency_ms,
                            request_id=request.metadata.get("request_id"),
                        )
                        self._circuit.record_success()
                        return
                    chunk = self._parse_stream_payload(
                        event_payload,
                        request=request,
                        started=started,
                        first_token_latency_ms=first_token_latency_ms,
                    )
                    if first_token_latency_ms is None and (
                        chunk.delta_text or chunk.tool_call_delta is not None
                    ):
                        first_token_latency_ms = _elapsed_ms(started)
                        chunk.first_token_latency_ms = first_token_latency_ms
                    if chunk.delta_text or chunk.tool_call_delta is not None:
                        emitted_any = True
                    yield chunk
            if emitted_any:
                raise ProviderStreamingError(
                    provider_name=self.provider_name,
                    model_name=self._model_for(request),
                    operation="text.stream",
                    retryable=True,
                    status_code=None,
                    safe_message="Provider stream ended before final marker.",
                )
            raise ProviderStreamingError(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                operation="text.stream",
                retryable=False,
                status_code=None,
                safe_message="Provider stream ended without data.",
            )
        except httpx.HTTPError as exc:
            self._circuit.record_failure(retryable=True)
            raise provider_error_from_httpx_exception(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                operation="text.stream",
                exc=exc,
                trace_id=request.metadata.get("trace_id"),
            ) from exc
        except Exception as exc:
            retryable = getattr(exc, "retryable", False)
            self._circuit.record_failure(retryable=bool(retryable))
            raise

    async def tool_call(self, request: TextGenerationRequest) -> TextGenerationResponse:
        if ProviderCapability.tool_calling not in self.capabilities:
            raise ProviderCapabilityError(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                operation="text.tool_call",
                retryable=False,
                status_code=None,
                safe_message="Text provider does not support tool calling.",
            )
        if not request.tools:
            raise ProviderBadRequestError(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                operation="text.tool_call",
                retryable=False,
                status_code=None,
                safe_message="Tool calling requires at least one tool definition.",
            )
        return await self.generate(request)

    def _build_chat_body(self, request: TextGenerationRequest, *, stream: bool) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self._model_for(request),
            "messages": [message_to_openai_dict(message) for message in self._messages(request)],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "max_tokens": request.max_output_tokens,
            "stream": stream,
        }
        if request.response_format == "json_object":
            body["response_format"] = {"type": "json_object"}
        elif request.response_format == "json_schema":
            if ProviderCapability.json_schema_output not in self.capabilities:
                if not self.settings.ai_text_allow_json_schema_downgrade:
                    raise ProviderCapabilityError(
                        provider_name=self.provider_name,
                        model_name=self._model_for(request),
                        operation="text.generate",
                        retryable=False,
                        status_code=None,
                        safe_message="Provider does not support JSON schema output.",
                    )
                body["response_format"] = {"type": "json_object"}
            else:
                body["response_format"] = {
                    "type": "json_schema",
                    "json_schema": request.json_schema,
                }
        if request.tools:
            body["tools"] = [tool.model_dump(mode="json") for tool in request.tools]
            body["tool_choice"] = request.tool_choice
        body.update(self.settings.ai_text_provider_extra_json)
        return body

    def _messages(self, request: TextGenerationRequest) -> list[ChatMessage]:
        if request.system_prompt is None:
            return list(request.messages)
        if request.messages and request.messages[0].role == MessageRole.system:
            return list(request.messages)
        return [
            ChatMessage(role=MessageRole.system, content=request.system_prompt),
            *request.messages,
        ]

    def _headers(self, request: TextGenerationRequest | None) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if request is not None:
            request_id = request.metadata.get("request_id")
            traceparent = request.metadata.get("traceparent")
            if request_id:
                headers["X-Request-Id"] = request_id
            if traceparent:
                headers["traceparent"] = traceparent
        return headers

    def _parse_chat_response(
        self,
        value: dict[str, Any],
        *,
        request: TextGenerationRequest,
        started: float,
        first_token_latency_ms: int | None,
    ) -> TextGenerationResponse:
        choices = value.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderResponseValidationError(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                operation="text.generate",
                retryable=False,
                status_code=None,
                safe_message="Provider response did not include choices.",
            )
        first = choices[0]
        if not isinstance(first, dict):
            raise ProviderResponseValidationError(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                operation="text.generate",
                retryable=False,
                status_code=None,
                safe_message="Provider response choice was invalid.",
            )
        message = first.get("message") or {}
        if not isinstance(message, dict):
            message = {}
        tool_calls = parse_openai_tool_calls(message.get("tool_calls"))
        content = message.get("content") or ""
        if not content and not tool_calls:
            raise ProviderResponseValidationError(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                operation="text.generate",
                retryable=False,
                status_code=None,
                safe_message="Provider response did not include content or tool calls.",
            )
        return TextGenerationResponse(
            provider_name=self.provider_name,
            model_name=self._model_for(request),
            content=str(content),
            finish_reason=parse_finish_reason(first.get("finish_reason")),
            tool_calls=tool_calls,
            usage=parse_usage(value.get("usage")),
            latency_ms=_elapsed_ms(started),
            first_token_latency_ms=first_token_latency_ms,
            request_id=str(value.get("id")) if value.get("id") is not None else None,
            raw_response_hash=safe_hash_json(value),
        )

    def _parse_stream_payload(
        self,
        payload: str,
        *,
        request: TextGenerationRequest,
        started: float,
        first_token_latency_ms: int | None,
    ) -> TextGenerationChunk:
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ProviderStreamingError(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                operation="text.stream",
                retryable=False,
                status_code=None,
                safe_message="Provider stream included invalid JSON.",
                internal_message=str(exc),
            ) from exc
        choices = value.get("choices")
        if not isinstance(choices, list) or not choices:
            return TextGenerationChunk(
                provider_name=self.provider_name,
                model_name=self._model_for(request),
                usage=parse_usage(value.get("usage")),
                request_id=str(value.get("id")) if value.get("id") is not None else None,
            )
        first = choices[0]
        delta = first.get("delta") if isinstance(first, dict) else {}
        if not isinstance(delta, dict):
            delta = {}
        tool_delta = delta.get("tool_calls")
        normalized_tool_delta = _normalize_tool_delta(tool_delta)
        return TextGenerationChunk(
            provider_name=self.provider_name,
            model_name=self._model_for(request),
            delta_text=str(delta.get("content") or ""),
            tool_call_delta=normalized_tool_delta,
            is_final=False,
            finish_reason=parse_finish_reason(first.get("finish_reason")),
            usage=parse_usage(value.get("usage")),
            latency_ms=_elapsed_ms(started),
            first_token_latency_ms=first_token_latency_ms,
            request_id=str(value.get("id")) if value.get("id") is not None else None,
        )

    def _model_for(self, request: TextGenerationRequest) -> str:
        return request.model or self.model_name

    def _chat_url(self) -> str:
        return _join_api_path(self.base_url, "chat/completions")

    def _models_url(self) -> str:
        return _join_api_path(self.base_url, "models")


async def iter_sse_data_lines(lines: AsyncIterator[str]) -> AsyncIterator[str]:
    async for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(":"):
            continue
        if stripped.startswith("data:"):
            yield stripped[5:].strip()


def message_to_openai_dict(message: ChatMessage) -> dict[str, str]:
    payload = {"role": message.role.value, "content": message.content}
    if message.name:
        payload["name"] = message.name
    if message.tool_call_id:
        payload["tool_call_id"] = message.tool_call_id
    return payload


def parse_openai_tool_calls(value: object) -> list[ToolCall]:
    if not isinstance(value, list):
        return []
    calls: list[ToolCall] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        function = item.get("function")
        if not isinstance(function, dict):
            continue
        name = str(function.get("name") or "")
        arguments_json = str(function.get("arguments") or "{}")
        calls.append(
            ToolCall.from_arguments_json(
                id=str(item.get("id") or ""),
                name=name,
                arguments_json=arguments_json,
            )
        )
    return calls


def _normalize_tool_delta(value: object) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"tool_calls": value}
    return None


def parse_usage(value: object) -> TokenUsage | None:
    if not isinstance(value, dict):
        return None
    return TokenUsage(
        prompt_tokens=_int_or_none(value.get("prompt_tokens")),
        completion_tokens=_int_or_none(value.get("completion_tokens")),
        total_tokens=_int_or_none(value.get("total_tokens")),
    )


def parse_finish_reason(value: object) -> TextGenerationFinishReason:
    if value == "stop":
        return TextGenerationFinishReason.stop
    if value == "length":
        return TextGenerationFinishReason.length
    if value == "tool_calls":
        return TextGenerationFinishReason.tool_calls
    if value == "content_filter":
        return TextGenerationFinishReason.content_filter
    if value is None:
        return TextGenerationFinishReason.unknown
    return TextGenerationFinishReason.unknown


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _join_api_path(base_url: str, suffix: str) -> str:
    normalized = base_url.rstrip("/") + "/"
    return urljoin(normalized, suffix)


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _now() -> Any:
    from datetime import UTC, datetime

    return datetime.now(UTC)
