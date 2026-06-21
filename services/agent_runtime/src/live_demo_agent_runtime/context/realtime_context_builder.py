"""Build compact grounded context for the realtime host agent."""

from dataclasses import replace
from typing import Any, Protocol

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.context.context_budget import ContextSection, pack_sections
from live_demo_agent_runtime.context.context_packager import render_context_json
from live_demo_agent_runtime.context.context_types import (
    BuildRealtimeContextRequest,
    ContextBudgetReport,
    ContextSource,
    KnowledgeFactContext,
    PersonaContext,
    ProductSummaryContext,
    RealtimeAgentContext,
    RecentTurnContext,
    RecipeStepContext,
    SafeActionContext,
    ScreenContext,
)
from live_demo_agent_runtime.context.knowledge_context import (
    rank_knowledge_facts,
    should_retrieve_knowledge,
)
from live_demo_agent_runtime.context.recipe_context import clamp_recipe_step
from live_demo_agent_runtime.context.safety_context import build_safety_rules
from live_demo_agent_runtime.context.screen_context import contains_forbidden_prompt_data
from live_demo_agent_runtime.context.source_attribution import (
    source_for_knowledge,
    source_for_product_summary,
    source_for_recipe_step,
    source_for_safe_action,
    source_for_screen,
)
from live_demo_agent_runtime.context.transcript_context import recent_turn_window


class RealtimeContextDataSource(Protocol):
    async def get_demo_phase(self, request: BuildRealtimeContextRequest) -> str: ...

    async def get_current_screen(
        self,
        request: BuildRealtimeContextRequest,
    ) -> ScreenContext | None: ...

    async def get_safe_actions(
        self,
        request: BuildRealtimeContextRequest,
    ) -> list[SafeActionContext]: ...

    async def get_active_recipe_step(
        self,
        request: BuildRealtimeContextRequest,
    ) -> RecipeStepContext | None: ...

    async def get_recent_turns(
        self,
        request: BuildRealtimeContextRequest,
        limit: int,
    ) -> list[RecentTurnContext]: ...

    async def get_persona(self, request: BuildRealtimeContextRequest) -> PersonaContext: ...

    async def get_product_summary(
        self,
        request: BuildRealtimeContextRequest,
    ) -> ProductSummaryContext | None: ...

    async def search_knowledge(
        self,
        request: BuildRealtimeContextRequest,
        top_k: int,
    ) -> list[KnowledgeFactContext]: ...


class InMemoryRealtimeContextDataSource:
    def __init__(
        self,
        *,
        demo_phase: str = "START",
        screen: ScreenContext | None = None,
        safe_actions: tuple[SafeActionContext, ...] = (),
        recipe_step: RecipeStepContext | None = None,
        recent_turns: tuple[RecentTurnContext, ...] = (),
        persona: PersonaContext | None = None,
        product_summary: ProductSummaryContext | None = None,
        knowledge: tuple[KnowledgeFactContext, ...] = (),
    ) -> None:
        self.demo_phase = demo_phase
        self.screen = screen
        self.safe_actions = safe_actions
        self.recipe_step = recipe_step
        self.recent_turns = recent_turns
        self.persona = persona or PersonaContext()
        self.product_summary = product_summary
        self.knowledge = knowledge

    async def get_demo_phase(self, request: BuildRealtimeContextRequest) -> str:
        del request
        return self.demo_phase

    async def get_current_screen(
        self,
        request: BuildRealtimeContextRequest,
    ) -> ScreenContext | None:
        del request
        return self.screen

    async def get_safe_actions(
        self,
        request: BuildRealtimeContextRequest,
    ) -> list[SafeActionContext]:
        del request
        return list(self.safe_actions)

    async def get_active_recipe_step(
        self,
        request: BuildRealtimeContextRequest,
    ) -> RecipeStepContext | None:
        del request
        return self.recipe_step

    async def get_recent_turns(
        self,
        request: BuildRealtimeContextRequest,
        limit: int,
    ) -> list[RecentTurnContext]:
        del request
        return list(self.recent_turns[-limit:])

    async def get_persona(self, request: BuildRealtimeContextRequest) -> PersonaContext:
        del request
        return self.persona

    async def get_product_summary(
        self,
        request: BuildRealtimeContextRequest,
    ) -> ProductSummaryContext | None:
        del request
        return self.product_summary

    async def search_knowledge(
        self,
        request: BuildRealtimeContextRequest,
        top_k: int,
    ) -> list[KnowledgeFactContext]:
        del request
        return list(self.knowledge[:top_k])


class RealtimeContextBuilder:
    def __init__(
        self,
        *,
        settings: AgentRuntimeSettings,
        data_source: RealtimeContextDataSource,
    ) -> None:
        self._settings = settings
        self._data_source = data_source

    async def build_context(
        self,
        request: BuildRealtimeContextRequest,
    ) -> RealtimeAgentContext:
        screen = await self._data_source.get_current_screen(request)
        if screen is not None and contains_forbidden_prompt_data(screen.summary):
            screen = ScreenContext(
                screen_id=screen.screen_id,
                screen_hash=screen.screen_hash,
                url_path=screen.url_path,
                title=screen.title,
                summary="[screen summary omitted: unsafe prompt data]",
                confidence=0.0,
                screenshot_artifact_id=screen.screenshot_artifact_id,
                updated_at=screen.updated_at,
            )
        screen = _truncate_screen(screen, self._settings.agent_context_max_screen_summary_chars)
        safe_actions = tuple(
            sorted(
                await self._data_source.get_safe_actions(request),
                key=lambda item: (-item.score, item.action_id),
            )[: self._settings.agent_context_max_safe_actions]
        )
        recipe_step = clamp_recipe_step(
            await self._data_source.get_active_recipe_step(request),
            self._settings.agent_context_max_recipe_step_chars,
        )
        recent_turns = recent_turn_window(
            await self._data_source.get_recent_turns(
                request,
                self._settings.agent_context_max_recent_turns,
            ),
            max_turns=self._settings.agent_context_max_recent_turns,
        )
        persona = await self._data_source.get_persona(request)
        product_summary = _truncate_product_summary(
            await self._data_source.get_product_summary(request),
            self._settings.agent_context_max_product_summary_chars,
        )
        retrieval_needed = (
            request.include_retrieval
            and self._settings.agent_knowledge_retrieval_enabled
            and (
                not self._settings.agent_knowledge_retrieval_only_on_demand
                or should_retrieve_knowledge(request.user_utterance, screen)
            )
        )
        retrieved_knowledge: tuple[KnowledgeFactContext, ...] = ()
        if retrieval_needed:
            facts = await self._data_source.search_knowledge(
                request,
                self._settings.agent_knowledge_retrieval_top_k,
            )
            retrieved_knowledge = rank_knowledge_facts(
                facts,
                top_k=self._settings.agent_context_max_retrieved_facts,
                min_score=self._settings.agent_knowledge_retrieval_min_score,
            )
        sources = self._build_source_map(
            screen=screen,
            safe_actions=safe_actions,
            recipe_step=recipe_step,
            product_summary=product_summary,
            knowledge=retrieved_knowledge,
        )
        safety_rules = build_safety_rules(self._settings)
        context = RealtimeAgentContext(
            organization_id=request.organization_id,
            demo_session_id=request.demo_session_id,
            product_id=request.product_id,
            active_turn_id=request.active_turn_id,
            demo_phase=await self._data_source.get_demo_phase(request),
            user_utterance=request.user_utterance,
            current_screen=screen,
            safe_actions=safe_actions,
            active_recipe_step=recipe_step,
            recent_turns=recent_turns,
            persona=persona,
            product_summary=product_summary,
            retrieved_knowledge=retrieved_knowledge,
            safety_rules=safety_rules,
            token_budget_report=ContextBudgetReport(
                max_tokens=self._settings.agent_context_max_tokens,
                estimated_tokens=0,
            ),
            source_map=tuple(sources),
        )
        context = self._fit_token_budget(context)
        report = self._budget_report(context)
        return RealtimeAgentContext(
            organization_id=context.organization_id,
            demo_session_id=context.demo_session_id,
            product_id=context.product_id,
            active_turn_id=context.active_turn_id,
            demo_phase=context.demo_phase,
            user_utterance=context.user_utterance,
            current_screen=context.current_screen,
            safe_actions=context.safe_actions,
            active_recipe_step=context.active_recipe_step,
            recent_turns=context.recent_turns,
            persona=context.persona,
            product_summary=context.product_summary,
            retrieved_knowledge=context.retrieved_knowledge,
            safety_rules=context.safety_rules,
            token_budget_report=report,
            source_map=context.source_map,
        )

    def _fit_token_budget(self, context: RealtimeAgentContext) -> RealtimeAgentContext:
        max_tokens = self._settings.agent_context_max_tokens
        dropped: list[str] = []
        truncated: list[str] = list(context.token_budget_report.truncated_sections)
        fitted = context

        def over_budget(candidate: RealtimeAgentContext) -> bool:
            return self._budget_report(candidate).estimated_tokens > max_tokens

        if over_budget(fitted) and fitted.retrieved_knowledge:
            dropped.append("retrieved_knowledge")
            fitted = _replace_context(fitted, retrieved_knowledge=())
        if over_budget(fitted) and fitted.product_summary is not None:
            dropped.append("product_summary")
            fitted = _replace_context(fitted, product_summary=None)
        if over_budget(fitted) and fitted.recent_turns:
            truncated.append("recent_turns")
            fitted = _replace_context(fitted, recent_turns=fitted.recent_turns[:2])
        if over_budget(fitted) and fitted.persona != PersonaContext():
            dropped.append("persona")
            fitted = _replace_context(fitted, persona=PersonaContext())
        if over_budget(fitted) and fitted.current_screen is not None:
            truncated.append("current_screen")
            fitted = _replace_context(
                fitted,
                current_screen=_truncate_screen(fitted.current_screen, 320),
            )
        report = self._budget_report(fitted)
        if report.estimated_tokens > max_tokens:
            report = ContextBudgetReport(
                max_tokens=max_tokens,
                estimated_tokens=report.estimated_tokens,
                truncated_sections=tuple((*report.truncated_sections, *truncated)),
                dropped_sections=tuple((*report.dropped_sections, *dropped)),
            )
        else:
            report = ContextBudgetReport(
                max_tokens=max_tokens,
                estimated_tokens=report.estimated_tokens,
                truncated_sections=tuple(sorted(set((*report.truncated_sections, *truncated)))),
                dropped_sections=tuple(sorted(set((*report.dropped_sections, *dropped)))),
            )
        return _replace_context(fitted, token_budget_report=report)

    def _budget_report(self, context: RealtimeAgentContext) -> ContextBudgetReport:
        prompt = render_context_json(context)
        packed = pack_sections(
            [
                ContextSection(
                    name="full_context",
                    content=prompt,
                    priority=1,
                    max_chars=self._settings.agent_context_max_tokens * 4,
                    required=True,
                )
            ],
            max_tokens=self._settings.agent_context_max_tokens,
        )
        return packed.report

    def _build_source_map(
        self,
        *,
        screen: ScreenContext | None,
        safe_actions: tuple[SafeActionContext, ...],
        recipe_step: RecipeStepContext | None,
        product_summary: ProductSummaryContext | None,
        knowledge: tuple[KnowledgeFactContext, ...],
    ) -> list[ContextSource]:
        sources: list[ContextSource] = []
        if screen is not None:
            sources.append(source_for_screen(screen))
        sources.extend(source_for_safe_action(action) for action in safe_actions)
        if recipe_step is not None:
            sources.append(source_for_recipe_step(recipe_step))
        if product_summary is not None:
            sources.append(source_for_product_summary(product_summary))
        sources.extend(source_for_knowledge(fact) for fact in knowledge)
        return sources


def _truncate_screen(screen: ScreenContext | None, max_chars: int) -> ScreenContext | None:
    if screen is None or len(screen.summary) <= max_chars:
        return screen
    return ScreenContext(
        screen_id=screen.screen_id,
        screen_hash=screen.screen_hash,
        url_path=screen.url_path,
        title=screen.title,
        summary=screen.summary[:max_chars].rstrip() + "[truncated]",
        confidence=screen.confidence,
        screenshot_artifact_id=screen.screenshot_artifact_id,
        updated_at=screen.updated_at,
    )


def _truncate_product_summary(
    product_summary: ProductSummaryContext | None,
    max_chars: int,
) -> ProductSummaryContext | None:
    if product_summary is None or len(product_summary.summary) <= max_chars:
        return product_summary
    return ProductSummaryContext(
        product_name=product_summary.product_name,
        product_url_domain=product_summary.product_url_domain,
        summary=product_summary.summary[:max_chars].rstrip() + "[truncated]",
        confidence=product_summary.confidence,
        source=product_summary.source,
    )


def _replace_context(
    context: RealtimeAgentContext,
    **changes: Any,
) -> RealtimeAgentContext:
    return replace(context, **changes)
