"""Health and readiness endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.dependencies import get_db_session, get_redis_client
from live_demo_api.health import get_health
from live_demo_api.observability.metrics import metrics

router = APIRouter(tags=["health"])
api_router = APIRouter(prefix="/api/v1", tags=["health"])


async def _ready_payload(db: AsyncSession, redis: Any) -> dict[str, object]:
    checks = {"database": "ok", "redis": "ok", "object_storage": "skipped"}
    await db.execute(text("select 1"))
    await redis.ping()
    return {
        "status": "ok",
        "service": "live-demo-api",
        "version": "0.1.0",
        "checks": checks,
    }


@router.get("/healthz")
async def healthz() -> dict[str, object]:
    return dict(get_health())


@router.get("/readyz")
async def readyz(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
) -> dict[str, object]:
    return await _ready_payload(db, redis)


@router.get("/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    return Response(content=metrics.prometheus_text(), media_type="text/plain; version=0.0.4")


@api_router.get("/healthz")
async def api_healthz() -> dict[str, object]:
    return dict(get_health())


@api_router.get("/readyz")
async def api_readyz(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
) -> dict[str, object]:
    return await _ready_payload(db, redis)
