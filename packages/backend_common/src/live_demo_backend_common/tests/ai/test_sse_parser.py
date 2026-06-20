from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest

from live_demo_backend_common.ai.errors import ProviderStreamingError
from live_demo_backend_common.ai.text.openai_compatible import (
    OpenAICompatibleTextProvider,
    iter_sse_data_lines,
)
from live_demo_backend_common.ai.types import ChatMessage, MessageRole, TextGenerationRequest
from live_demo_backend_common.tests.ai.helpers import mock_client, test_settings


async def _lines() -> AsyncIterator[str]:
    yield 'data: {"choices":[{"delta":{"content":"hi"}}]}'
    yield ""
    yield "data: [DONE]"


@pytest.mark.asyncio
async def test_sse_data_line_parser_handles_done() -> None:
    assert [item async for item in iter_sse_data_lines(_lines())] == [
        '{"choices":[{"delta":{"content":"hi"}}]}',
        "[DONE]",
    ]


@pytest.mark.asyncio
async def test_stream_yields_chunks_immediately_and_final() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=(
                b'data: {"id":"1","choices":[{"delta":{"content":"hi"},"finish_reason":null}]}\n\n'
                b"data: [DONE]\n\n"
            ),
        )

    provider = OpenAICompatibleTextProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key=None,
        model_name="demo-model",
        settings=test_settings(),
        client=mock_client(handler),
    )
    chunks = [
        chunk
        async for chunk in provider.stream(
            TextGenerationRequest(messages=[ChatMessage(role=MessageRole.user, content="hello")])
        )
    ]
    assert chunks[0].delta_text == "hi"
    assert chunks[0].first_token_latency_ms is not None
    assert chunks[-1].is_final is True


@pytest.mark.asyncio
async def test_stream_invalid_json_raises() -> None:
    provider = OpenAICompatibleTextProvider(
        provider_name="custom_openai_compatible",
        base_url="https://provider.test/v1",
        api_key=None,
        model_name="demo-model",
        settings=test_settings(),
        client=mock_client(lambda request: httpx.Response(200, content=b"data: not-json\n\n")),
    )
    with pytest.raises(ProviderStreamingError):
        [
            chunk
            async for chunk in provider.stream(
                TextGenerationRequest(
                    messages=[ChatMessage(role=MessageRole.user, content="hello")]
                )
            )
        ]
