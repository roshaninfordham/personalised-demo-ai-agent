"""Context source attribution helpers."""

from live_demo_agent_runtime.context.context_types import (
    ContextSource,
    KnowledgeFactContext,
    ProductSummaryContext,
    RecipeStepContext,
    SafeActionContext,
    ScreenContext,
)


def source_for_screen(screen: ScreenContext) -> ContextSource:
    return ContextSource(
        source_id=screen.screen_id,
        source_type="current_screen",
        confidence=screen.confidence,
        description="Current browser screen summary",
    )


def source_for_safe_action(action: SafeActionContext) -> ContextSource:
    return ContextSource(
        source_id=action.action_id,
        source_type="safe_action",
        confidence=action.score,
        description=f"Safe action: {action.label}",
    )


def source_for_recipe_step(step: RecipeStepContext) -> ContextSource:
    return ContextSource(
        source_id=step.step_key,
        source_type="recipe_step",
        confidence=1.0,
        description="Active demo recipe step",
    )


def source_for_product_summary(summary: ProductSummaryContext) -> ContextSource:
    return ContextSource(
        source_id=summary.source,
        source_type="product_summary",
        confidence=summary.confidence,
        description="Approved product summary",
    )


def source_for_knowledge(fact: KnowledgeFactContext) -> ContextSource:
    return ContextSource(
        source_id=fact.fact_id,
        source_type="knowledge_chunk",
        confidence=fact.score,
        description=fact.source,
    )
