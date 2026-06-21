"""Learner API service."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.db.models import ProductLearningRun
from live_demo_api.errors import NotFoundError
from live_demo_api.repositories.learner_jobs import LearnerRunRepository
from live_demo_api.repositories.products import ProductRepository
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.audit_service import AuditService

LOGGER = logging.getLogger(__name__)


class LearnerService:
    def __init__(self) -> None:
        self._audit = AuditService()

    async def create_learning_run(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        principal: Principal,
        *,
        product_id: UUID,
        trigger_type: str,
        start_url: str | None,
        session_id: UUID | None,
        request_context: RequestContext,
    ) -> dict[str, object]:
        settings = get_settings()
        async with db.begin():
            product = await ProductRepository(db).get_product(
                organization_id=principal.organization_id, product_id=product_id
            )
            if product is None:
                raise NotFoundError("Product not found.", code="product_not_found")
            run = await LearnerRunRepository(db).create_run(
                organization_id=principal.organization_id,
                product_id=product_id,
                session_id=session_id,
                start_url=start_url or product.product_url,
                trigger_type=trigger_type,
                max_attempts=settings.learner_max_attempts,
            )
            await self._audit.audit(
                db,
                principal=principal,
                action="learner.run.create",
                resource_type="product_learning_run",
                resource_id=run.learning_run_id,
            )
        if settings.learner_enabled:
            await self._enqueue(redis, run, request_context.trace_id)
        return _serialize_run(run)

    async def best_effort_enqueue_product_created(
        self,
        db: AsyncSession,
        redis: Redis[bytes],
        principal: Principal,
        *,
        product_id: UUID,
        product_url: str,
        request_context: RequestContext,
    ) -> None:
        try:
            await self.create_learning_run(
                db,
                redis,
                principal,
                product_id=product_id,
                trigger_type="product_created",
                start_url=product_url,
                session_id=None,
                request_context=request_context,
            )
        except Exception:
            LOGGER.exception(
                "learner.product_created_enqueue_failed", extra={"product_id": product_id}
            )

    async def _enqueue(self, redis: Redis[bytes], run: ProductLearningRun, trace_id: str) -> str:
        settings = get_settings()
        fields = {
            "job_id": str(uuid4()),
            "organization_id": str(run.organization_id),
            "product_id": str(run.product_id),
            "session_id": str(run.session_id or ""),
            "learning_run_id": str(run.learning_run_id),
            "job_type": "learn_product_from_url",
            "start_url": str(run.start_url),
            "priority": "50",
            "attempt": "1",
            "max_attempts": str(run.max_attempts),
            "created_at": datetime.now(UTC).isoformat(),
            "trace_id": trace_id,
            "payload": "{}",
        }
        raw_id = await redis.xadd(
            settings.learner_job_stream,
            fields,
            maxlen=settings.learner_job_enqueue_maxlen,
            approximate=True,
        )
        return raw_id.decode() if isinstance(raw_id, bytes) else str(raw_id)


def _serialize_run(run: ProductLearningRun) -> dict[str, object]:
    return {
        "learning_run_id": str(run.learning_run_id),
        "organization_id": str(run.organization_id),
        "product_id": str(run.product_id),
        "session_id": str(run.session_id) if run.session_id else None,
        "start_url": run.start_url,
        "status": run.status,
        "trigger_type": run.trigger_type,
        "attempt_count": run.attempt_count,
        "max_attempts": run.max_attempts,
        "error_code": run.error_code,
        "metrics": run.metrics,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
    }
