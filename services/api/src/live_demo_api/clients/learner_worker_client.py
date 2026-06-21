"""Learner worker client abstraction."""

from __future__ import annotations

from uuid import UUID, uuid5


class LearnerWorkerClient:
    async def enqueue_learning_run(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        session_id: UUID,
        start_url: str,
        trace_id: str,
    ) -> UUID:
        _ = organization_id, product_id, start_url, trace_id
        return uuid5(session_id, "learner-run")

    async def detach_or_cancel_run(self, *, learner_run_id: UUID, trace_id: str) -> bool:
        _ = learner_run_id, trace_id
        return True
