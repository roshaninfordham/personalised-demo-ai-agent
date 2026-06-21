from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

import pytest

from live_demo_backend_common.ai.embeddings.fake import FakeEmbeddingProvider
from live_demo_backend_common.policy.redaction import RedactionEngine
from live_demo_learner_worker.browser.browser_runtime_client import (
    FakeBrowserRuntimeClient,
    make_fixture_screen,
)
from live_demo_learner_worker.config import LearnerWorkerSettings
from live_demo_learner_worker.events.learner_event_publisher import LearnerEventPublisher
from live_demo_learner_worker.jobs.learner_job_types import LearnerJobEnvelope
from live_demo_learner_worker.knowledge.embedding_writer import EmbeddingWriter
from live_demo_learner_worker.worker.product_learning_orchestrator import (
    ProductLearningOrchestrator,
)


class FakeRedis:
    def __init__(self) -> None:
        self.events: list[dict[str, str]] = []

    async def xadd(
        self,
        stream: str,
        fields: dict[str, str],
        *,
        maxlen: int,
        approximate: bool,
    ) -> bytes:
        _ = (stream, maxlen, approximate)
        self.events.append(fields)
        return b"1-0"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fixture_dashboard_learning_run() -> None:
    organization_id = uuid4()
    product_id = uuid4()
    redis = cast(Any, FakeRedis())
    settings = LearnerWorkerSettings(first_screen_summary_use_llm=False, ai_embedding_dimensions=8)
    orchestrator = ProductLearningOrchestrator(
        settings=settings,
        browser_client=FakeBrowserRuntimeClient(
            [make_fixture_screen(organization_id=organization_id, product_id=product_id)]
        ),
        event_publisher=LearnerEventPublisher(redis),
        redaction_engine=RedactionEngine(),
        embedding_writer=EmbeddingWriter(FakeEmbeddingProvider(dimensions=8), dimensions=8),
    )
    job = LearnerJobEnvelope.create(
        organization_id=organization_id,
        product_id=product_id,
        learning_run_id=uuid4(),
        start_url="https://example.com",
        trace_id="trace",
    )

    result = await orchestrator.run(job)

    assert result.summary_ready
    assert result.category == "analytics_dashboard"
    assert result.chunk_count >= 1
    assert redis.events
