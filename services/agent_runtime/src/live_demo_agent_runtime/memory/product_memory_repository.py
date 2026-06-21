"""Product memory repository placeholder for future learner-owned facts."""

from uuid import UUID

from live_demo_agent_runtime.context.context_types import KnowledgeFactContext


class ProductMemoryRepository:
    async def search_product_memory(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        query: str,
        top_k: int,
    ) -> tuple[KnowledgeFactContext, ...]:
        del organization_id, product_id, query, top_k
        return ()
