from __future__ import annotations

import httpx
import pytest
from pydantic import SecretStr

from live_demo_backend_common.ai.errors import ProviderCapabilityError
from live_demo_backend_common.ai.text.nvidia_nim import NvidiaNimTextProvider
from live_demo_backend_common.ai.types import ChatMessage, MessageRole, TextGenerationRequest
from live_demo_backend_common.tests.ai.helpers import json_response, mock_client, test_settings


@pytest.mark.asyncio
async def test_nvidia_nim_uses_openai_compatible_endpoint_and_bearer_token() -> None:
    captured: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["authorization"] = request.headers.get("Authorization")
        return json_response(
            {"choices": [{"message": {"content": "nim response"}, "finish_reason": "stop"}]}
        )

    provider = NvidiaNimTextProvider(
        test_settings(
            ai_text_provider="nvidia_nim",
            ai_text_base_url="https://integrate.api.nvidia.com/v1",
            ai_text_api_key=SecretStr("nim-secret"),
            ai_text_model="meta/test",
        ),
        client=mock_client(handler),
    )
    response = await provider.generate(
        TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
    )
    assert captured["url"] == "https://integrate.api.nvidia.com/v1/chat/completions"
    assert captured["authorization"] == "Bearer nim-secret"
    assert response.content == "nim response"


@pytest.mark.asyncio
async def test_nvidia_nim_tool_calling_is_capability_gated() -> None:
    provider = NvidiaNimTextProvider(
        test_settings(
            ai_text_provider="nvidia_nim",
            ai_text_base_url="https://integrate.api.nvidia.com/v1",
            ai_text_model="meta/test",
            ai_text_enable_tool_calling=False,
        ),
        client=mock_client(lambda request: json_response({})),
    )
    with pytest.raises(ProviderCapabilityError):
        await provider.tool_call(
            TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
        )
