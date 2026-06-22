"""Redis Streams product learner worker loop."""

from __future__ import annotations

import logging
import os
import socket
import time
from uuid import UUID

from live_demo_backend_common.observability import metric_names, span_names
from live_demo_backend_common.observability.metrics import get_global_registry
from live_demo_backend_common.observability.trace_context import TraceContext
from live_demo_backend_common.observability.tracing import start_span
from live_demo_learner_worker.demo_graph.graph_repository import PostgresGraphRepository
from live_demo_learner_worker.dependencies import LearnerDependencies
from live_demo_learner_worker.events.event_types import (
    LEARNER_JOB_COMPLETED,
    LEARNER_JOB_FAILED,
    LEARNER_JOB_STARTED,
    LEARNER_STARTED,
)
from live_demo_learner_worker.jobs.dead_letter import dead_letter_job
from live_demo_learner_worker.jobs.idempotency import acquire_job_lock, release_job_lock
from live_demo_learner_worker.jobs.learner_job_queue import ReceivedLearnerJob
from live_demo_learner_worker.jobs.learner_job_repository import PostgresLearningRunRepository
from live_demo_learner_worker.jobs.learner_job_runner import LearnerJobRunner
from live_demo_learner_worker.jobs.learner_job_types import LearnerJobEnvelope
from live_demo_learner_worker.jobs.redis_stream_job_queue import RedisStreamLearnerJobQueue
from live_demo_learner_worker.jobs.retry_policy import retry_delay_ms
from live_demo_learner_worker.knowledge.chunk_repository import PostgresChunkRepository
from live_demo_learner_worker.knowledge.embedding_writer import EmbeddingWriter
from live_demo_learner_worker.routes.route_repository import PostgresRouteRepository
from live_demo_learner_worker.worker.product_learning_orchestrator import (
    ProductLearningOrchestrator,
)
from live_demo_learner_worker.worker.shutdown import ShutdownState

LOGGER = logging.getLogger(__name__)


class ProductLearnerWorker:
    def __init__(self, dependencies: LearnerDependencies) -> None:
        self._dependencies = dependencies
        settings = dependencies.settings
        self._queue = RedisStreamLearnerJobQueue(
            dependencies.redis,
            stream=settings.learner_job_stream,
            dead_letter_stream=settings.learner_dead_letter_stream,
            group=settings.learner_consumer_group,
            consumer=f"learner-worker-{socket.gethostname()}-{os.getpid()}",
            count=settings.learner_read_count,
            block_ms=settings.learner_block_ms,
            maxlen=settings.redis_event_stream_maxlen,
        )
        self._shutdown = ShutdownState()
        self._runner = LearnerJobRunner(
            ProductLearningOrchestrator(
                settings=settings,
                browser_client=dependencies.browser_client,
                event_publisher=dependencies.event_publisher,
                redaction_engine=dependencies.redaction_engine,
                embedding_writer=EmbeddingWriter(
                    dependencies.embedding_provider,
                    dimensions=settings.ai_embedding_dimensions,
                    batch_size=settings.knowledge_embedding_batch_size,
                ),
                run_repository=PostgresLearningRunRepository(dependencies.db_sessionmaker),
                graph_repository_factory=lambda job: PostgresGraphRepository(
                    dependencies.db_sessionmaker,
                    organization_id=job.organization_id,
                    product_id=job.product_id,
                ),
                route_repository_factory=lambda job: PostgresRouteRepository(
                    dependencies.db_sessionmaker,
                    organization_id=job.organization_id,
                    learning_run_id=job.learning_run_id,
                ),
                chunk_repository=PostgresChunkRepository(dependencies.db_sessionmaker),
            )
        )

    async def run_forever(self) -> None:
        await self._queue.ensure_group()
        if not self._dependencies.settings.learner_enabled:
            return
        await self._dependencies.event_publisher.publish(
            event_type=LEARNER_STARTED,
            organization_id=_local_org_id(),
            product_id=_local_product_id(),
            learning_run_id=None,
            session_id=None,
            trace_id="learner-startup",
            payload={"status": "ready"},
        )
        while not self._shutdown.draining:
            received_jobs = await self._queue.read()
            for received in received_jobs:
                await self._handle_job(received.message_id, received.job)

    async def stop(self) -> None:
        self._shutdown.request_stop()

    async def _handle_job(self, message_id: str, job: object) -> None:
        if not isinstance(job, LearnerJobEnvelope):
            await self._queue.ack(message_id)
            return
        started_ns = time.perf_counter_ns()
        registry = get_global_registry()
        trace_context = (
            TraceContext(trace_id=job.trace_id, span_id=job.job_id.hex[:16])
            if len(job.trace_id) == 32
            else TraceContext.new()
        )
        locked = await acquire_job_lock(
            self._dependencies.redis,
            job_id=job.job_id,
            ttl_seconds=self._dependencies.settings.learner_job_lock_ttl_seconds,
        )
        if not locked:
            await self._queue.ack(message_id)
            return
        with start_span(
            span_names.LEARNER_JOB_PROCESS,
            trace_context=trace_context,
            attributes={
                "live_demo.organization_id": str(job.organization_id),
                "live_demo.product_id": str(job.product_id),
                "live_demo.session_id": str(job.session_id) if job.session_id else "",
                "live_demo.operation": job.job_type.value,
            },
        ):
            try:
                await self._publish(job, LEARNER_JOB_STARTED, {"attempt": job.attempt})
                await self._runner.run(job)
                registry.increment(
                    metric_names.LEARNER_JOBS_TOTAL,
                    labels={"job_type": job.job_type.value, "result": "success"},
                )
                registry.observe(
                    metric_names.LEARNER_JOB_DURATION_SECONDS,
                    (time.perf_counter_ns() - started_ns) / 1_000_000_000,
                    labels={"job_type": job.job_type.value, "result": "success"},
                )
                await self._publish(job, LEARNER_JOB_COMPLETED, {"attempt": job.attempt})
                await self._queue.ack(message_id)
            except Exception as exc:
                registry.increment(
                    metric_names.LEARNER_JOBS_TOTAL,
                    labels={"job_type": job.job_type.value, "result": "failed"},
                )
                registry.observe(
                    metric_names.LEARNER_JOB_DURATION_SECONDS,
                    (time.perf_counter_ns() - started_ns) / 1_000_000_000,
                    labels={"job_type": job.job_type.value, "result": "failed"},
                )
                await self._handle_failure(message_id, job, exc)
            finally:
                await release_job_lock(self._dependencies.redis, job_id=job.job_id)

    async def _handle_failure(
        self, message_id: str, job: LearnerJobEnvelope, exc: Exception
    ) -> None:
        error_code = getattr(exc, "code", "learner_job_failed")
        retryable = bool(getattr(exc, "retryable", True))
        if retryable and job.attempt < job.max_attempts:
            delay = retry_delay_ms(
                job_id=job.job_id,
                attempt=job.attempt,
                base_delay_ms=self._dependencies.settings.learner_retry_base_delay_ms,
                max_delay_ms=self._dependencies.settings.learner_retry_max_delay_ms,
            )
            _ = delay
            await self._queue.enqueue(job.next_attempt())
            await self._queue.ack(message_id)
            await self._publish(
                job, LEARNER_JOB_FAILED, {"retrying": True, "error_code": error_code}
            )
            return
        await dead_letter_job(
            self._queue,
            ReceivedLearnerJob(message_id=message_id, job=job),
            error_code=error_code,
        )
        await self._queue.ack(message_id)
        await self._publish(job, LEARNER_JOB_FAILED, {"retrying": False, "error_code": error_code})

    async def _publish(
        self, job: LearnerJobEnvelope, event_type: str, payload: dict[str, object]
    ) -> None:
        await self._dependencies.event_publisher.publish(
            event_type=event_type,
            organization_id=job.organization_id,
            product_id=job.product_id,
            learning_run_id=job.learning_run_id,
            session_id=job.session_id,
            trace_id=job.trace_id,
            payload=payload,
        )


def _local_org_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


def _local_product_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000020")
