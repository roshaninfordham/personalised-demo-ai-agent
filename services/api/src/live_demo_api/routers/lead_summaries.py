"""Lead insight, lead-summary, and CRM payload API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.dependencies import get_current_principal, get_db_session
from live_demo_api.security import Principal
from live_demo_api.services.lead_summary_service import LeadSummaryService
from live_demo_contracts.lead_summary import (
    CrmPayloadResponse,
    LeadInsightsResponse,
    LeadSummaryResponse,
)

router = APIRouter(prefix="/api/v1/demo-sessions/{session_id}", tags=["lead-summaries"])


@router.get("/lead-insights", response_model=LeadInsightsResponse)
async def get_lead_insights(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    insight_type: str | None = None,
    min_confidence: float | None = None,
    limit: Annotated[int | None, Query(ge=1)] = None,
    cursor: str | None = None,
) -> LeadInsightsResponse:
    return await LeadSummaryService().list_insights(
        db,
        principal,
        session_id,
        insight_type=insight_type,
        min_confidence=min_confidence,
        limit=limit,
        cursor=cursor,
    )


@router.get("/lead-summary", response_model=LeadSummaryResponse)
async def get_lead_summary(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> LeadSummaryResponse:
    return await LeadSummaryService().get_summary(db, principal, session_id)


@router.get("/crm-payload", response_model=CrmPayloadResponse)
async def get_crm_payload(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> CrmPayloadResponse:
    return await LeadSummaryService().get_crm_payload(db, principal, session_id)
