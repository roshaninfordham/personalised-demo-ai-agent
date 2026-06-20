from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from live_demo_backend_common.ai.types import (
    ProviderCapability,
    ProviderHealth,
    ProviderStatus,
    TextGenerationChunk,
    TextGenerationFinishReason,
    TextGenerationRequest,
    TextGenerationResponse,
    ToolCall,
)


class FakeTextProvider:
    provider_name = "fake"
    model_name = "fake-text-model"
    capabilities = frozenset(
        {
            ProviderCapability.text_generate,
            ProviderCapability.text_stream,
            ProviderCapability.tool_calling,
            ProviderCapability.json_schema_output,
        }
    )

    async def close(self) -> None:
        return None

    async def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.provider_name,
            provider_type="text",
            model_name=self.model_name,
            status=ProviderStatus.healthy,
            capabilities=list(self.capabilities),
            checked_at=datetime.now(UTC),
            safe_message="Fake text provider is healthy.",
        )

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResponse:
        return TextGenerationResponse(
            provider_name=self.provider_name,
            model_name=request.model or self.model_name,
            content=request.metadata.get("fake_response", "fake response"),
            finish_reason=TextGenerationFinishReason.stop,
            latency_ms=0,
            request_id=request.metadata.get("request_id"),
        )

    async def stream(self, request: TextGenerationRequest) -> AsyncIterator[TextGenerationChunk]:
        for delta in ["fake", " ", "response"]:
            yield TextGenerationChunk(
                provider_name=self.provider_name,
                model_name=request.model or self.model_name,
                delta_text=delta,
                is_final=False,
                latency_ms=0,
                first_token_latency_ms=0,
                request_id=request.metadata.get("request_id"),
            )
        yield TextGenerationChunk(
            provider_name=self.provider_name,
            model_name=request.model or self.model_name,
            is_final=True,
            finish_reason=TextGenerationFinishReason.stop,
            latency_ms=0,
            first_token_latency_ms=0,
            request_id=request.metadata.get("request_id"),
        )

    async def tool_call(self, request: TextGenerationRequest) -> TextGenerationResponse:
        tool_calls: list[ToolCall] = []
        if request.tools:
            tool_calls.append(
                ToolCall(
                    id="fake_tool_call_1",
                    name=request.tools[0].function.name,
                    arguments_json="{}",
                    arguments={},
                )
            )
        return TextGenerationResponse(
            provider_name=self.provider_name,
            model_name=request.model or self.model_name,
            content="",
            finish_reason=(
                TextGenerationFinishReason.tool_calls
                if tool_calls
                else TextGenerationFinishReason.stop
            ),
            tool_calls=tool_calls,
            latency_ms=0,
            request_id=request.metadata.get("request_id"),
        )
