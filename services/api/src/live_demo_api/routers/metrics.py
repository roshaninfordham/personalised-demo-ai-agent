"""Lightweight local metrics summary API."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.config import get_settings
from live_demo_api.db.models import ActionEvent, DemoSession
from live_demo_api.db.types import SessionStatus
from live_demo_api.dependencies import get_current_principal, get_db_session
from live_demo_api.security import Principal

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


class MetricsSummaryResponse(BaseModel):
    active_sessions: int
    sessions_today: int
    browser_actions_today: int
    policy_blocks_today: int
    average_prewarm_ms: float | None
    average_browser_action_ms: float | None
    event_lag_ms: float | None
    observability_enabled: bool
    grafana_url: str
    prometheus_url: str


@router.get("/summary", response_model=MetricsSummaryResponse)
async def metrics_summary(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> MetricsSummaryResponse:
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    active_statuses = [
        SessionStatus.CREATED.value,
        SessionStatus.PREWARMING.value,
        SessionStatus.WAITING_FOR_USER.value,
        SessionStatus.LIVE.value,
        SessionStatus.ENDING.value,
    ]
    active_sessions = await db.scalar(
        select(func.count())
        .select_from(DemoSession)
        .where(
            DemoSession.organization_id == principal.organization_id,
            DemoSession.deleted_at.is_(None),
            DemoSession.status.in_(active_statuses),
        )
    )
    sessions_today = await db.scalar(
        select(func.count())
        .select_from(DemoSession)
        .where(
            DemoSession.organization_id == principal.organization_id,
            DemoSession.deleted_at.is_(None),
            DemoSession.created_at >= today,
        )
    )
    actions_today = await db.scalar(
        select(func.count())
        .select_from(ActionEvent)
        .where(
            ActionEvent.organization_id == principal.organization_id,
            ActionEvent.created_at >= today,
        )
    )
    policy_blocks_today = await db.scalar(
        select(func.count())
        .select_from(ActionEvent)
        .where(
            ActionEvent.organization_id == principal.organization_id,
            ActionEvent.created_at >= today,
            ActionEvent.policy_decision == "blocked",
        )
    )
    avg_action_latency = await db.scalar(
        select(func.avg(ActionEvent.latency_ms)).where(
            ActionEvent.organization_id == principal.organization_id,
            ActionEvent.created_at >= today,
            ActionEvent.latency_ms.is_not(None),
        )
    )
    settings = get_settings()
    average_browser_action_ms = (
        float(avg_action_latency) if avg_action_latency is not None else None
    )
    return MetricsSummaryResponse(
        active_sessions=int(active_sessions or 0),
        sessions_today=int(sessions_today or 0),
        browser_actions_today=int(actions_today or 0),
        policy_blocks_today=int(policy_blocks_today or 0),
        average_prewarm_ms=None,
        average_browser_action_ms=average_browser_action_ms,
        event_lag_ms=None,
        observability_enabled=bool(settings.enable_tracing),
        grafana_url="http://localhost:3001",
        prometheus_url="http://localhost:9090",
    )
