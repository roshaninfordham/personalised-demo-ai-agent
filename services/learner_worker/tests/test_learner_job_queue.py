from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from live_demo_learner_worker.jobs.learner_job_types import (
    LearnerJobEnvelope,
    LearnerJobType,
)
from live_demo_learner_worker.jobs.retry_policy import retry_delay_ms


def test_job_envelope_round_trip() -> None:
    job = LearnerJobEnvelope(
        job_id=uuid4(),
        organization_id=UUID("00000000-0000-0000-0000-000000000001"),
        product_id=UUID("00000000-0000-0000-0000-000000000002"),
        session_id=None,
        learning_run_id=UUID("00000000-0000-0000-0000-000000000003"),
        job_type=LearnerJobType.LEARN_PRODUCT_FROM_URL,
        start_url="https://example.com",
        priority=50,
        attempt=1,
        max_attempts=3,
        created_at=datetime.now(UTC),
        trace_id="trace",
    )

    parsed = LearnerJobEnvelope.from_mapping(job.to_mapping())

    assert parsed.job_id == job.job_id
    assert parsed.job_type == LearnerJobType.LEARN_PRODUCT_FROM_URL


def test_retry_backoff_is_deterministic() -> None:
    job_id = UUID("00000000-0000-0000-0000-000000000010")
    assert retry_delay_ms(
        job_id=job_id, attempt=2, base_delay_ms=1000, max_delay_ms=60000
    ) == retry_delay_ms(job_id=job_id, attempt=2, base_delay_ms=1000, max_delay_ms=60000)
