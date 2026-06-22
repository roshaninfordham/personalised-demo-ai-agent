"""Post-demo job envelope types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class PostDemoJobEnvelope:
    job_id: UUID
    organization_id: UUID
    session_id: UUID
    job_type: str
    attempt: int
    max_attempts: int
    idempotency_key: str
    created_at: datetime
    trace_id: str
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def full_run(
        cls,
        *,
        organization_id: UUID,
        session_id: UUID,
        trace_id: str,
        max_attempts: int,
    ) -> PostDemoJobEnvelope:
        return cls(
            job_id=uuid4(),
            organization_id=organization_id,
            session_id=session_id,
            job_type="run_full_post_demo_intelligence",
            attempt=1,
            max_attempts=max_attempts,
            idempotency_key=f"session:{session_id}:post_demo:v1",
            created_at=datetime.now(UTC),
            trace_id=trace_id,
        )
