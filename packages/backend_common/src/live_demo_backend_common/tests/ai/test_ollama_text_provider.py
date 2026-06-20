from __future__ import annotations

import httpx
import pytest

from live_demo_backend_common.ai.errors import ProviderCapabilityError
from live_demo_backend_common.ai.text.ollama import OllamaTextProvider
from live_demo_backend_common.ai.types import ChatMessage, MessageRole, TextGenerationRequest
from live_demo_backend_common.tests.ai.helpers import json_response, mock_client, test_settings


@pytest.mark.asyncio
async def test_ollama_openai_compatible_mode_delegates() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return json_response({"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]})

    provider = OllamaTextProvider(
        test_settings(
            ai_text_provider="ollama",
            ollama_base_url="http://ollama:11434",
            ollama_text_model="llama3",
            ollama_text_mode="openai_compatible",
        ),
        client=mock_client(handler),
    )
    response = await provider.generate(
        TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
    )
    assert captured["url"] == "http://ollama:11434/v1/chat/completions"
    assert response.content == "ok"


@pytest.mark.asyncio
async def test_ollama_native_mode_calls_api_chat_and_streams_json_lines() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://ollama:11434/api/chat"
        if b'"stream":true' in request.read():
            return httpx.Response(
                200,
                content=(
                    b'{"message":{"content":"he"},"done":false}\n'
                    b'{"message":{"content":"llo"},"done":true}\n'
                ),
            )
        return json_response({"message": {"content": "hello"}, "done": True})

    provider = OllamaTextProvider(
        test_settings(
            ai_text_provider="ollama",
            ollama_base_url="http://ollama:11434",
            ollama_text_model="llama3",
            ollama_text_mode="native",
        ),
        client=mock_client(handler),
    )
    response = await provider.generate(
        TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
    )
    assert response.content == "hello"
    chunks = [
        chunk
        async for chunk in provider.stream(
            TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
        )
    ]
    assert "".join(chunk.delta_text for chunk in chunks) == "hello"
    assert chunks[-1].is_final is True

    with pytest.raises(ProviderCapabilityError):
        await provider.tool_call(
            TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
        )
