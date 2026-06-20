from __future__ import annotations

import httpx
import pytest

from live_demo_backend_common.ai.errors import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseValidationError,
)
from live_demo_backend_common.ai.text.openai_compatible import OpenAICompatibleTextProvider
from live_demo_backend_common.ai.types import (
    ChatMessage,
    MessageRole,
    TextGenerationRequest,
    ToolDefinition,
    ToolFunctionSchema,
)
from live_demo_backend_common.tests.ai.helpers import json_response, mock_client, test_settings


@pytest.mark.asyncio
async def test_maps_request_and_parses_content_response() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        captured["request_id"] = request.headers.get("X-Request-Id")
        captured["traceparent"] = request.headers.get("traceparent")
        return json_response(
            {
                "id": "chatcmpl_1",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "hello"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
            }
        )

    provider = OpenAICompatibleTextProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key="secret-key",
        model_name="demo-model",
        settings=test_settings(ai_text_provider="custom_openai_compatible"),
        client=mock_client(handler),
    )
    response = await provider.generate(
        TextGenerationRequest(
            system_prompt="system",
            messages=[ChatMessage(role=MessageRole.user, content="say hello")],
            metadata={"request_id": "req_1", "traceparent": "00-ab-cd-01"},
        )
    )

    assert captured["url"] == "https://provider.test/v1/chat/completions"
    assert captured["request_id"] == "req_1"
    assert captured["traceparent"] == "00-ab-cd-01"
    assert b'"role":"system"' in captured["body"]  # type: ignore[operator]
    assert response.content == "hello"
    assert response.usage is not None
    assert response.usage.total_tokens == 3
    assert response.raw_response_hash is not None


@pytest.mark.asyncio
async def test_parses_tool_calls() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert b'"tools":' in request.read()
        return json_response(
            {
                "id": "chatcmpl_2",
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "read_current_screen",
                                        "arguments": '{"screen_id":"1"}',
                                    },
                                }
                            ]
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
            }
        )

    provider = OpenAICompatibleTextProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key=None,
        model_name="demo-model",
        settings=test_settings(),
        client=mock_client(handler),
    )
    response = await provider.tool_call(
        TextGenerationRequest(
            messages=[ChatMessage(role=MessageRole.user, content="use tool")],
            tools=[
                ToolDefinition(
                    function=ToolFunctionSchema(
                        name="read_current_screen",
                        description="Read screen.",
                        parameters={"type": "object", "properties": {}},
                    )
                )
            ],
        )
    )
    assert response.tool_calls[0].arguments == {"screen_id": "1"}


@pytest.mark.asyncio
async def test_missing_choices_raises_validation_error() -> None:
    provider = OpenAICompatibleTextProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key=None,
        model_name="demo-model",
        settings=test_settings(),
        client=mock_client(lambda request: json_response({"id": "bad"})),
    )
    with pytest.raises(ProviderResponseValidationError):
        await provider.generate(
            TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
        )


@pytest.mark.asyncio
async def test_http_errors_are_normalized() -> None:
    provider_401 = OpenAICompatibleTextProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key="secret",
        model_name="demo-model",
        settings=test_settings(),
        client=mock_client(lambda request: json_response({"error": "bad key"}, status_code=401)),
    )
    with pytest.raises(ProviderAuthenticationError):
        await provider_401.generate(
            TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
        )

    provider_429 = OpenAICompatibleTextProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key="secret",
        model_name="demo-model",
        settings=test_settings(),
        client=mock_client(lambda request: json_response({"error": "rate"}, status_code=429)),
    )
    with pytest.raises(ProviderRateLimitError):
        await provider_429.generate(
            TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
        )
