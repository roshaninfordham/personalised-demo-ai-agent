"""Learning run repository interface for worker internals."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@dataclass(slots=True)
class InMemoryLearningRunRepository:
    statuses: dict[UUID, str] = field(default_factory=dict)

    async def mark_running(self, learning_run_id: UUID) -> None:
        self.statuses[learning_run_id] = "running"

    async def mark_completed(self, learning_run_id: UUID) -> None:
        self.statuses[learning_run_id] = "completed"

    async def mark_failed(self, learning_run_id: UUID, error_code: str) -> None:
        self.statuses[learning_run_id] = f"failed:{error_code}"


@dataclass(slots=True)
class PostgresLearningRunRepository:
    sessionmaker: async_sessionmaker[AsyncSession]

    async def mark_running(self, learning_run_id: UUID) -> None:
        async with self.sessionmaker() as session, session.begin():
            await session.execute(
                text(
                    """
                    UPDATE product_learning_runs
                    SET status = 'running',
                        started_at = COALESCE(started_at, now()),
                        updated_at = now(),
                        attempt_count = attempt_count + 1
                    WHERE learning_run_id = :learning_run_id
                    """
                ),
                {"learning_run_id": learning_run_id},
            )

    async def mark_completed(self, learning_run_id: UUID) -> None:
        async with self.sessionmaker() as session, session.begin():
            await session.execute(
                text(
                    """
                    UPDATE product_learning_runs
                    SET status = 'completed',
                        finished_at = now(),
                        updated_at = now(),
                        error_code = NULL,
                        error_message = NULL
                    WHERE learning_run_id = :learning_run_id
                    """
                ),
                {"learning_run_id": learning_run_id},
            )

    async def mark_failed(self, learning_run_id: UUID, error_code: str) -> None:
        async with self.sessionmaker() as session, session.begin():
            await session.execute(
                text(
                    """
                    UPDATE product_learning_runs
                    SET status = 'failed',
                        finished_at = now(),
                        updated_at = now(),
                        error_code = :error_code
                    WHERE learning_run_id = :learning_run_id
                    """
                ),
                {"learning_run_id": learning_run_id, "error_code": error_code},
            )
