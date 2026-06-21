"""Lead insight persistence boundary.

Phase 8 keeps this repository interface lightweight. The runtime tests use the
in-memory implementation; a DB-backed implementation can map these records to
the Phase 2 lead_insights table without changing the agent brain.
"""

from collections import defaultdict
from uuid import UUID

from live_demo_agent_runtime.memory.memory_types import StoredMemory


class LeadInsightRepository:
    async def list_for_session(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
    ) -> tuple[StoredMemory, ...]:
        raise NotImplementedError

    async def upsert_memory(self, memory: StoredMemory) -> StoredMemory:
        raise NotImplementedError


class InMemoryLeadInsightRepository(LeadInsightRepository):
    def __init__(self) -> None:
        self._items: dict[tuple[UUID, UUID], list[StoredMemory]] = defaultdict(list)

    async def list_for_session(
        self,
        *,
        organization_id: UUID,
        demo_session_id: UUID,
    ) -> tuple[StoredMemory, ...]:
        return tuple(self._items[(organization_id, demo_session_id)])

    async def upsert_memory(self, memory: StoredMemory) -> StoredMemory:
        key = (memory.organization_id, memory.demo_session_id)
        items = self._items[key]
        for index, existing in enumerate(items):
            if existing.memory_id == memory.memory_id:
                items[index] = memory
                return memory
        items.append(memory)
        return memory
