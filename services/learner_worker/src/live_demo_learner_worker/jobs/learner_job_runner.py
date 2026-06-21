"""Learner job runner."""

from __future__ import annotations

from live_demo_learner_worker.jobs.learner_job_types import LearnerJobEnvelope
from live_demo_learner_worker.worker.product_learning_orchestrator import (
    ProductLearningOrchestrator,
)


class LearnerJobRunner:
    def __init__(self, orchestrator: ProductLearningOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def run(self, job: LearnerJobEnvelope) -> None:
        await self._orchestrator.run(job)
