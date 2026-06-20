"""Health and readiness endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.dependencies import get_db_session, get_redis_client
from live_demo_api.health import get_health

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


@api_router.get("/healthz")
async def api_healthz() -> dict[str, object]:
    return dict(get_health())


@api_router.get("/readyz")
async def api_readyz(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Any, Depends(get_redis_client)],
) -> dict[str, object]:
    return await _ready_payload(db, redis)
