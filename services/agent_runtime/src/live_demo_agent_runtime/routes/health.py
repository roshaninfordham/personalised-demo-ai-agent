"""Health and readiness routes."""

from fastapi import APIRouter
from fastapi.responses import Response

from live_demo_agent_runtime.db.session import ping_database
from live_demo_agent_runtime.health import health_check
from live_demo_agent_runtime.redis.redis_client import ping_redis
from live_demo_backend_common.observability.metrics import get_global_registry

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return health_check()


@router.get("/readyz")
async def readyz() -> dict[str, object]:
    database_ok = False
    redis_ok = False
    try:
        database_ok = await ping_database()
    except Exception:
        database_ok = False
    try:
        redis_ok = await ping_redis()
    except Exception:
        redis_ok = False
    checks = {
        "database": database_ok,
        "redis": redis_ok,
    }
    return {
        "status": "ok" if all(checks.values()) else "degraded",
        "checks": checks,
    }


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(
        content=get_global_registry().render_prometheus(),
        media_type="text/plain; version=0.0.4",
    )
