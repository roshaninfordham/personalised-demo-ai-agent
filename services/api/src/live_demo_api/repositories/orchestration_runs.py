"""Repository for session orchestration run records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import SessionOrchestrationRun


class OrchestrationRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        run_type: str,
        trace_id: str,
    ) -> SessionOrchestrationRun:
        row = SessionOrchestrationRun(
            organization_id=organization_id,
            session_id=session_id,
            run_type=run_type,
            status="running",
            attempt_count=1,
            started_at=datetime.now(UTC),
            trace_id=trace_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def finish_run(
        self,
        row: SessionOrchestrationRun,
        *,
        status: str,
        metrics: dict[str, object] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> SessionOrchestrationRun:
        row.status = status
        row.metrics = metrics or row.metrics or {}
        row.error_code = error_code
        row.error_message = error_message
        row.finished_at = datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        await self._session.flush()
        return row

    async def latest_for_session(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        run_type: str | None = None,
    ) -> SessionOrchestrationRun | None:
        statement = select(SessionOrchestrationRun).where(
            SessionOrchestrationRun.organization_id == organization_id,
            SessionOrchestrationRun.session_id == session_id,
        )
        if run_type is not None:
            statement = statement.where(SessionOrchestrationRun.run_type == run_type)
        statement = statement.order_by(SessionOrchestrationRun.created_at.desc()).limit(1)
        return cast(SessionOrchestrationRun | None, await self._session.scalar(statement))
