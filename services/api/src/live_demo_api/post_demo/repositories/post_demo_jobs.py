"""Post-demo job repository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import PostDemoJob


class PostDemoJobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert_running(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        job_type: str,
        idempotency_key: str,
        trace_id: str,
        max_attempts: int,
    ) -> PostDemoJob:
        now = datetime.now(UTC)
        statement = (
            insert(PostDemoJob)
            .values(
                organization_id=organization_id,
                session_id=session_id,
                job_type=job_type,
                idempotency_key=idempotency_key,
                trace_id=trace_id,
                max_attempts=max_attempts,
                status="running",
                started_at=now,
            )
            .on_conflict_do_update(
                constraint="uq_post_demo_jobs_idempotency",
                set_={
                    "status": "running",
                    "started_at": now,
                    "updated_at": now,
                },
            )
            .returning(PostDemoJob)
        )
        return (await self._db.scalars(statement)).one()

    async def mark_completed(
        self, job: PostDemoJob, *, metrics: dict[str, object] | None = None
    ) -> None:
        job.status = "completed"
        job.finished_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
        job.metrics = metrics or {}
