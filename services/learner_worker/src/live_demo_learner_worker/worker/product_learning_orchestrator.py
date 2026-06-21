"""Cold-path product learning orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from live_demo_backend_common.policy.redaction import RedactionEngine
from live_demo_learner_worker.browser.browser_runtime_client import BrowserRuntimeClient
from live_demo_learner_worker.classification.product_category_detector import (
    ProductCategoryDetector,
)
from live_demo_learner_worker.config import LearnerWorkerSettings
from live_demo_learner_worker.demo_graph.action_edge_builder import build_action_edge
from live_demo_learner_worker.demo_graph.graph_builder import DemoGraphBuilder
from live_demo_learner_worker.demo_graph.graph_repository import InMemoryGraphRepository
from live_demo_learner_worker.demo_graph.graph_types import DemoGraphActionEdge, DemoGraphScreenNode
from live_demo_learner_worker.events.event_types import (
    LEARNER_ACTION_EXPLORATION_COMPLETED,
    LEARNER_DEMO_GRAPH_UPDATED,
    LEARNER_DEMO_ROUTE_GENERATED,
    LEARNER_FIRST_SCREEN_LOADED,
    LEARNER_KNOWLEDGE_CHUNKED,
    LEARNER_PRODUCT_CATEGORY_DETECTED,
    LEARNER_SCREEN_SUMMARY_READY,
)
from live_demo_learner_worker.events.learner_event_publisher import LearnerEventPublisher
from live_demo_learner_worker.exploration.candidate_action_explorer import CandidateActionExplorer
from live_demo_learner_worker.exploration.exploration_limits import ExplorationLimits
from live_demo_learner_worker.exploration.exploration_policy import ExplorationPolicy
from live_demo_learner_worker.jobs.learner_job_repository import InMemoryLearningRunRepository
from live_demo_learner_worker.jobs.learner_job_types import LearnerJobEnvelope
from live_demo_learner_worker.knowledge.chunk_deduper import ChunkDeduper
from live_demo_learner_worker.knowledge.chunk_repository import InMemoryChunkRepository
from live_demo_learner_worker.knowledge.chunk_types import KnowledgeChunk, KnowledgeChunkInput
from live_demo_learner_worker.knowledge.embedding_writer import EmbeddingWriter
from live_demo_learner_worker.knowledge.knowledge_chunker import KnowledgeChunker
from live_demo_learner_worker.routes.generated_route_builder import GeneratedRouteBuilder
from live_demo_learner_worker.routes.route_repository import InMemoryRouteRepository
from live_demo_learner_worker.routes.route_types import GeneratedDemoRoute
from live_demo_learner_worker.summarization.first_screen_summarizer import FirstScreenSummarizer
from live_demo_learner_worker.summarization.screen_summary_types import FirstScreenSummaryInput


@dataclass(slots=True)
class ProductLearningResult:
    summary_ready: bool
    category: str
    graph_node_count: int
    graph_edge_count: int
    route_created: bool
    chunk_count: int


class LearningRunRepository(Protocol):
    async def mark_running(self, learning_run_id: UUID) -> None: ...
    async def mark_completed(self, learning_run_id: UUID) -> None: ...
    async def mark_failed(self, learning_run_id: UUID, error_code: str) -> None: ...


class GraphRepository(Protocol):
    async def upsert_screen_node(
        self, node: DemoGraphScreenNode, *, organization_id: UUID | None = None
    ) -> DemoGraphScreenNode: ...

    async def upsert_action_edge(
        self, edge: DemoGraphActionEdge, *, organization_id: UUID | None = None
    ) -> DemoGraphActionEdge: ...

    async def get_graph_for_product(
        self,
    ) -> tuple[list[DemoGraphScreenNode], list[DemoGraphActionEdge]]: ...


class RouteRepository(Protocol):
    async def save_route(
        self, route: GeneratedDemoRoute, *, organization_id: UUID | None = None
    ) -> GeneratedDemoRoute: ...


class ChunkRepository(Protocol):
    async def upsert_chunks(
        self, chunks: tuple[KnowledgeChunk, ...]
    ) -> tuple[KnowledgeChunk, ...]: ...


class ProductLearningOrchestrator:
    def __init__(
        self,
        *,
        settings: LearnerWorkerSettings,
        browser_client: BrowserRuntimeClient,
        event_publisher: LearnerEventPublisher,
        redaction_engine: RedactionEngine,
        embedding_writer: EmbeddingWriter,
        run_repository: LearningRunRepository | None = None,
        graph_repository: GraphRepository | None = None,
        graph_repository_factory: Callable[[LearnerJobEnvelope], GraphRepository] | None = None,
        route_repository: RouteRepository | None = None,
        route_repository_factory: Callable[[LearnerJobEnvelope], RouteRepository] | None = None,
        chunk_repository: ChunkRepository | None = None,
    ) -> None:
        self._settings = settings
        self._browser_client = browser_client
        self._event_publisher = event_publisher
        self._redaction_engine = redaction_engine
        self._embedding_writer = embedding_writer
        self._run_repository = run_repository or InMemoryLearningRunRepository()
        self._graph_repository = graph_repository or InMemoryGraphRepository()
        self._graph_repository_factory = graph_repository_factory
        self._route_repository = route_repository or InMemoryRouteRepository()
        self._route_repository_factory = route_repository_factory
        self._chunk_repository = chunk_repository or InMemoryChunkRepository()

    async def run(self, job: LearnerJobEnvelope) -> ProductLearningResult:
        await self._run_repository.mark_running(job.learning_run_id)
        graph_repository = (
            self._graph_repository_factory(job)
            if self._graph_repository_factory is not None
            else self._graph_repository
        )
        route_repository = (
            self._route_repository_factory(job)
            if self._route_repository_factory is not None
            else self._route_repository
        )
        screen_read = await self._browser_client.read_current_screen(job.product_id)
        await self._publish(
            job, LEARNER_FIRST_SCREEN_LOADED, {"screen_hash": screen_read.screen_state.screen_hash}
        )

        summary = await FirstScreenSummarizer(
            use_llm=self._settings.first_screen_summary_use_llm
        ).summarize(
            FirstScreenSummaryInput(
                organization_id=job.organization_id,
                product_id=job.product_id,
                session_id=job.session_id,
                screen_state=screen_read.screen_state,
                ui_elements=screen_read.ui_elements,
                visible_text=screen_read.screen_state.visible_text,
                safe_actions=screen_read.safe_actions,
                screenshot_artifact_id=screen_read.screen_state.screenshot_artifact_id,
                trace_id=job.trace_id,
            )
        )
        await self._publish(
            job,
            LEARNER_SCREEN_SUMMARY_READY,
            {
                "screen_id": str(summary.screen_id),
                "summary": summary.summary,
                "confidence": summary.confidence,
                "safe_action_count": len(screen_read.safe_actions),
            },
        )

        detector = ProductCategoryDetector(self._settings.product_category_min_confidence)
        category = detector.detect(
            screen_summary=summary.summary,
            visible_text=screen_read.screen_state.visible_text,
            elements=screen_read.ui_elements,
            product_name=None,
            guidance_text=None,
            safe_actions=screen_read.safe_actions,
        )
        await self._publish(
            job,
            LEARNER_PRODUCT_CATEGORY_DETECTED,
            {
                "category": category.category,
                "confidence": category.confidence,
                "demo_angles": list(category.demo_angles),
            },
        )

        explorer = CandidateActionExplorer(
            self._browser_client,
            ExplorationPolicy(
                only_low_risk_actions=self._settings.learner_only_low_risk_actions,
                allow_form_submit=self._settings.learner_allow_form_submit,
                allow_typing=self._settings.learner_allow_typing,
                allow_external_navigation=self._settings.learner_allow_external_navigation,
            ),
            ExplorationLimits(
                max_pages_per_product=self._settings.learner_max_pages_per_product,
                max_depth=self._settings.learner_max_depth,
                max_actions_per_screen=self._settings.learner_max_actions_per_screen,
                max_total_actions=self._settings.learner_max_total_actions,
                max_recovery_attempts=self._settings.learner_max_recovery_attempts,
            ),
        )
        outcome = await explorer.explore(screen_read)
        await self._publish(
            job,
            LEARNER_ACTION_EXPLORATION_COMPLETED,
            {
                "attempted": outcome.attempted,
                "skipped": outcome.skipped,
                "succeeded": outcome.succeeded,
                "visited_screens": outcome.visited_screens,
            },
        )

        graph_builder = DemoGraphBuilder()
        node = graph_builder.upsert_screen(screen_read, screen_type=summary.screen_type)
        node = await graph_repository.upsert_screen_node(node, organization_id=job.organization_id)
        for action in screen_read.safe_actions:
            result = await self._browser_client.execute_action(action)
            to_node = (
                await graph_repository.upsert_screen_node(
                    graph_builder.upsert_screen(result.resulting_screen),
                    organization_id=job.organization_id,
                )
                if result.resulting_screen
                else None
            )
            edge = build_action_edge(
                from_node=node,
                to_node=to_node,
                action=action,
                latency_ms=result.latency_ms,
                success=result.success,
            )
            await graph_repository.upsert_action_edge(edge, organization_id=job.organization_id)
            graph_builder.graph.edges.append(edge)
        nodes, edges = await graph_repository.get_graph_for_product()
        await self._publish(
            job, LEARNER_DEMO_GRAPH_UPDATED, {"node_count": len(nodes), "edge_count": len(edges)}
        )

        route = GeneratedRouteBuilder(max_steps=self._settings.generated_route_max_steps).build(
            product_id=job.product_id, nodes=nodes, edges=edges
        )
        route_created = route.confidence >= self._settings.generated_route_min_confidence
        if route_created:
            await route_repository.save_route(route, organization_id=job.organization_id)
            await self._publish(
                job,
                LEARNER_DEMO_ROUTE_GENERATED,
                {"route_id": str(route.route_id), "confidence": route.confidence},
            )

        chunker = KnowledgeChunker(
            self._redaction_engine,
            max_chars=self._settings.knowledge_chunk_max_chars,
            overlap_chars=self._settings.knowledge_chunk_overlap_chars,
            min_chars=self._settings.knowledge_chunk_min_chars,
        )
        chunk_input = KnowledgeChunkInput(
            organization_id=job.organization_id,
            product_id=job.product_id,
            source_type="screen_summary",
            source_id=str(screen_read.screen_state.screen_id),
            source_uri=screen_read.screen_state.url,
            title=screen_read.screen_state.title,
            content=summary.summary,
            metadata={"screen_type": summary.screen_type},
            confidence=summary.confidence,
        )
        chunks = ChunkDeduper().dedupe(chunker.chunk(chunk_input))
        embedded = await self._embedding_writer.embed_chunks(chunks) if chunks else ()
        await self._chunk_repository.upsert_chunks(embedded)
        await self._publish(job, LEARNER_KNOWLEDGE_CHUNKED, {"chunk_count": len(embedded)})
        await self._run_repository.mark_completed(job.learning_run_id)
        return ProductLearningResult(
            summary_ready=True,
            category=category.category,
            graph_node_count=len(nodes),
            graph_edge_count=len(edges),
            route_created=route_created,
            chunk_count=len(embedded),
        )

    async def _publish(
        self,
        job: LearnerJobEnvelope,
        event_type: str,
        payload: dict[str, object],
    ) -> None:
        await self._event_publisher.publish(
            event_type=event_type,
            organization_id=job.organization_id,
            product_id=job.product_id,
            learning_run_id=job.learning_run_id,
            session_id=job.session_id,
            trace_id=job.trace_id,
            payload=payload,
        )
