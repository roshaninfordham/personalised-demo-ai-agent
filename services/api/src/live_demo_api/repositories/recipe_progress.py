from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import DemoStep, RecipeGenerationRun, RecipeStepProgress


class RecipeProgressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def initialize_steps(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        recipe_id: UUID,
        steps: list[DemoStep],
    ) -> list[RecipeStepProgress]:
        for step in steps:
            statement = (
                insert(RecipeStepProgress)
                .values(
                    organization_id=organization_id,
                    session_id=session_id,
                    recipe_id=recipe_id,
                    step_id=step.step_id,
                    step_key=step.step_key,
                    status="pending",
                    evidence={},
                )
                .on_conflict_do_nothing(
                    index_elements=[RecipeStepProgress.session_id, RecipeStepProgress.step_id]
                )
            )
            await self._session.execute(statement)
        await self._session.flush()
        return await self.list_progress(organization_id=organization_id, session_id=session_id)

    async def list_progress(
        self, *, organization_id: UUID, session_id: UUID
    ) -> list[RecipeStepProgress]:
        statement = (
            select(RecipeStepProgress)
            .where(
                RecipeStepProgress.organization_id == organization_id,
                RecipeStepProgress.session_id == session_id,
            )
            .order_by(RecipeStepProgress.created_at.asc())
        )
        return list((await self._session.scalars(statement)).all())

    async def update_step(
        self,
        *,
        organization_id: UUID,
        session_id: UUID,
        step_key: str,
        status: str,
        matched_screen_id: UUID | None = None,
        matched_action_id: str | None = None,
        matched_confidence: float = 0.0,
        failure_reason: str | None = None,
        evidence: dict[str, object] | None = None,
    ) -> RecipeStepProgress | None:
        rows = await self.list_progress(organization_id=organization_id, session_id=session_id)
        row = next((item for item in rows if item.step_key == step_key), None)
        if row is None:
            return None
        now = datetime.now(UTC)
        row.status = status
        row.updated_at = now
        if status == "in_progress":
            row.started_at = row.started_at or now
            row.attempt_count += 1
        elif status == "completed":
            row.completed_at = now
        elif status == "skipped":
            row.skipped_at = now
        elif status == "failed":
            row.failed_at = now
            row.attempt_count += 1
        if matched_screen_id is not None:
            row.matched_screen_id = matched_screen_id
        if matched_action_id is not None:
            row.matched_action_id = matched_action_id
        row.matched_confidence = Decimal(
            str(max(float(row.matched_confidence), matched_confidence))
        )
        if failure_reason is not None:
            row.failure_reason = failure_reason
        if evidence:
            row.evidence = {**(row.evidence or {}), **evidence}
        await self._session.flush()
        return row


class RecipeGenerationRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_run(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        input_hash: str,
        source_guidance_id: UUID | None = None,
        provider: str | None = "deterministic",
        model: str | None = "fallback",
    ) -> RecipeGenerationRun:
        row = RecipeGenerationRun(
            organization_id=organization_id,
            product_id=product_id,
            source_guidance_id=source_guidance_id,
            status="running",
            provider=provider,
            model=model,
            input_hash=input_hash,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def finish_run(
        self,
        row: RecipeGenerationRun,
        *,
        status: str,
        output_hash: str | None,
        validation_passed: bool | None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> RecipeGenerationRun:
        row.status = status
        row.output_hash = output_hash
        row.validation_passed = validation_passed
        row.error_code = error_code
        row.error_message = error_message
        row.finished_at = datetime.now(UTC)
        await self._session.flush()
        return row
