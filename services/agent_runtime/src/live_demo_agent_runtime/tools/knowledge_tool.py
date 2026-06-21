"""Knowledge tool helper."""

from live_demo_agent_runtime.context.context_types import KnowledgeFactContext
from live_demo_agent_runtime.context.knowledge_context import rank_knowledge_facts


async def search_product_knowledge(
    facts: list[KnowledgeFactContext],
    *,
    top_k: int,
    min_score: float,
) -> tuple[KnowledgeFactContext, ...]:
    return rank_knowledge_facts(facts, top_k=top_k, min_score=min_score)
