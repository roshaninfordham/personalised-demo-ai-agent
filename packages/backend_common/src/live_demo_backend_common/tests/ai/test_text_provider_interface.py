from __future__ import annotations

import pytest

from live_demo_backend_common.ai.text.fake import FakeTextProvider
from live_demo_backend_common.ai.types import (
    ChatMessage,
    MessageRole,
    TextGenerationFinishReason,
    TextGenerationRequest,
    ToolDefinition,
    ToolFunctionSchema,
)


@pytest.mark.asyncio
async def test_fake_text_provider_generate_stream_and_tool_call() -> None:
    provider = FakeTextProvider()
    request = TextGenerationRequest(
        messages=[ChatMessage(role=MessageRole.user, content="hello")],
        metadata={"fake_response": "deterministic"},
    )

    response = await provider.generate(request)
    assert response.content == "deterministic"

    chunks = [chunk async for chunk in provider.stream(request)]
    assert "".join(chunk.delta_text for chunk in chunks) == "fake response"
    assert chunks[-1].is_final is True

    tool_response = await provider.tool_call(
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
    assert tool_response.finish_reason == TextGenerationFinishReason.tool_calls
    assert tool_response.tool_calls[0].name == "read_current_screen"

    health = await provider.health_check()
    assert health.status == "healthy"
