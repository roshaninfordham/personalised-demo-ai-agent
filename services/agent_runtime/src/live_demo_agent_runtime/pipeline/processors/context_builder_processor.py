"""Pipeline wrapper around realtime context building."""

from live_demo_agent_runtime.context.context_types import (
    BuildRealtimeContextRequest,
    RealtimeAgentContext,
)
from live_demo_agent_runtime.context.realtime_context_builder import RealtimeContextBuilder


class ContextBuilderProcessor:
    def __init__(self, context_builder: RealtimeContextBuilder) -> None:
        self._context_builder = context_builder

    async def process(self, request: BuildRealtimeContextRequest) -> RealtimeAgentContext:
        return await self._context_builder.build_context(request)
