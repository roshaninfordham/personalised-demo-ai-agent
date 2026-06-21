"""Application factory for health probes and embedded worker startup."""

from __future__ import annotations

from fastapi import FastAPI

from live_demo_learner_worker.config import get_settings
from live_demo_learner_worker.health import health_check, readiness_check


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Live Demo Learner Worker", version="0.1.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return health_check()

    @app.get("/readyz")
    async def readyz() -> dict[str, str]:
        return readiness_check(settings.learner_enabled)

    return app
