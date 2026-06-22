"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from redis.asyncio import Redis

from live_demo_api.config import get_settings
from live_demo_api.db.session import dispose_database_engine, get_async_engine, get_sessionmaker
from live_demo_api.errors import register_error_handlers
from live_demo_api.events.redis_stream_event_bus import RedisStreamEventBus
from live_demo_api.logging_config import configure_logging
from live_demo_api.middleware import setup_middleware
from live_demo_api.observability.setup import setup_observability
from live_demo_api.observability.tracing import configure_tracing
from live_demo_api.routers import (
    artifacts,
    audit_logs,
    demo,
    demo_sessions,
    guidance,
    health,
    lead_summaries,
    learner,
    metrics,
    policy_debug,
    products,
    recipes,
    transcripts,
)
from live_demo_api.storage.s3_artifact_store import S3ArtifactStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    setup_observability(settings)
    get_async_engine()
    get_sessionmaker()
    redis: Any = Redis.from_url(settings.redis_url)
    app.state.redis = redis
    app.state.event_bus = RedisStreamEventBus(redis)
    artifact_store = S3ArtifactStore(settings)
    app.state.artifact_store = artifact_store
    if settings.object_storage_auto_create_bucket:
        if settings.app_env == "production" and not settings.allow_production_bucket_create:
            logger.warning("object_storage.bucket_create_skipped_production")
        else:
            await artifact_store.ensure_bucket()
    logger.info("api.startup", extra={"settings": settings.safe_log_dict()})
    try:
        yield
    finally:
        await redis.close()
        await dispose_database_engine()
        logger.info("api.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    docs_url = "/docs" if settings.api_enable_docs else None
    redoc_url = "/redoc" if settings.api_enable_docs else None
    app = FastAPI(
        title="Live Demo Agent API",
        version="0.1.0",
        description="Backend API for live AI product-demo agent platform.",
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
    )
    setup_middleware(app, settings)
    register_error_handlers(app)
    configure_tracing(app, settings.enable_tracing)
    app.include_router(health.router)
    app.include_router(health.api_router)
    app.include_router(demo.router)
    app.include_router(artifacts.router)
    app.include_router(products.router)
    app.include_router(guidance.router)
    app.include_router(recipes.router)
    app.include_router(demo_sessions.router)
    app.include_router(demo_sessions.product_router)
    app.include_router(transcripts.router)
    app.include_router(lead_summaries.router)
    app.include_router(learner.router)
    app.include_router(audit_logs.router)
    app.include_router(metrics.router)
    if settings.policy_debug_endpoints_enabled:
        app.include_router(policy_debug.router)
    return app
