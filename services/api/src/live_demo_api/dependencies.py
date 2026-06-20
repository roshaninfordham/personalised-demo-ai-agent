"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, cast

from fastapi import Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.db.session import get_sessionmaker
from live_demo_api.events.event_bus import EventBus
from live_demo_api.security import Principal, RequestContext, parse_principal_headers
from live_demo_api.storage.artifact_store import ArtifactStore


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session


def get_redis_client(request: Request) -> Any:
    return request.app.state.redis


def get_event_bus(request: Request) -> EventBus:
    return cast(EventBus, request.app.state.event_bus)


def get_artifact_store(request: Request) -> ArtifactStore:
    return cast(ArtifactStore, request.app.state.artifact_store)


def get_request_context(request: Request) -> RequestContext:
    return RequestContext(
        request_id=str(getattr(request.state, "request_id", "")),
        trace_id=str(getattr(request.state, "trace_id", "")),
    )


def get_current_principal(
    x_organization_id: str | None = Header(default=None, alias="X-Organization-ID"),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> Principal:
    return parse_principal_headers(
        organization_id=x_organization_id,
        user_id=x_user_id,
        role=x_user_role,
        settings=get_settings(),
    )
