"""Learner job queue protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from live_demo_learner_worker.jobs.learner_job_types import LearnerJobEnvelope


@dataclass(frozen=True, slots=True)
class ReceivedLearnerJob:
    message_id: str
    job: LearnerJobEnvelope


class LearnerJobQueue(Protocol):
    async def ensure_group(self) -> None: ...

    async def enqueue(self, job: LearnerJobEnvelope) -> str: ...

    async def read(self) -> tuple[ReceivedLearnerJob, ...]: ...

    async def ack(self, message_id: str) -> None: ...

    async def dead_letter(self, received: ReceivedLearnerJob, error_code: str) -> str: ...
