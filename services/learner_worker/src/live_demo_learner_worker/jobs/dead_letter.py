"""Dead-letter helpers."""

from __future__ import annotations

from live_demo_learner_worker.jobs.learner_job_queue import LearnerJobQueue, ReceivedLearnerJob


async def dead_letter_job(
    queue: LearnerJobQueue,
    received: ReceivedLearnerJob,
    *,
    error_code: str,
) -> str:
    return await queue.dead_letter(received, error_code)
