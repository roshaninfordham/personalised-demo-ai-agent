"""Learner run repositories."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import ProductLearningRun


class LearnerRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        start_url: str,
        trigger_type: str,
        session_id: UUID | None = None,
        max_attempts: int = 3,
    ) -> ProductLearningRun:
        row = ProductLearningRun(
            organization_id=organization_id,
            product_id=product_id,
            session_id=session_id,
            start_url=start_url,
            trigger_type=trigger_type,
            max_attempts=max_attempts,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_run(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        learning_run_id: UUID,
    ) -> ProductLearningRun | None:
        return cast(
            ProductLearningRun | None,
            await self._session.scalar(
                sa.select(ProductLearningRun).where(
                    ProductLearningRun.organization_id == organization_id,
                    ProductLearningRun.product_id == product_id,
                    ProductLearningRun.learning_run_id == learning_run_id,
                )
            ),
        )

    async def list_runs(
        self, *, organization_id: UUID, product_id: UUID, limit: int
    ) -> list[ProductLearningRun]:
        return list(
            (
                await self._session.scalars(
                    sa.select(ProductLearningRun)
                    .where(
                        ProductLearningRun.organization_id == organization_id,
                        ProductLearningRun.product_id == product_id,
                    )
                    .order_by(
                        ProductLearningRun.created_at.desc(),
                        ProductLearningRun.learning_run_id.desc(),
                    )
                    .limit(limit)
                )
            ).all()
        )

    async def mark_running(self, learning_run_id: UUID) -> None:
        await self._session.execute(
            sa.update(ProductLearningRun)
            .where(ProductLearningRun.learning_run_id == learning_run_id)
            .values(status="running", started_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        )

    async def mark_completed(
        self, learning_run_id: UUID, metrics: dict[str, object] | None = None
    ) -> None:
        await self._session.execute(
            sa.update(ProductLearningRun)
            .where(ProductLearningRun.learning_run_id == learning_run_id)
            .values(
                status="completed",
                finished_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                metrics=metrics or {},
            )
        )
