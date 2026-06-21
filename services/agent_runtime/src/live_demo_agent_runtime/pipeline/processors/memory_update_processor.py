"""Pipeline wrapper around memory updates."""

from collections.abc import Iterable
from uuid import UUID

from live_demo_agent_runtime.memory.memory_types import MemoryHandleResult, MemoryUpdate
from live_demo_agent_runtime.memory.memory_update_handler import MemoryUpdateHandler


class MemoryUpdateProcessor:
    def __init__(self, handler: MemoryUpdateHandler) -> None:
        self._handler = handler

    async def process(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
        updates: Iterable[MemoryUpdate],
        trace_id: str,
    ) -> MemoryHandleResult:
        return await self._handler.handle_updates(
            organization_id=organization_id,
            demo_session_id=demo_session_id,
            updates=updates,
            trace_id=trace_id,
        )
