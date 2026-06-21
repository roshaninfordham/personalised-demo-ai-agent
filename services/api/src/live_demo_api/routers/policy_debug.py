"""Internal policy debug routes for local development."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from live_demo_api.dependencies import get_current_principal
from live_demo_api.security import Principal

router = APIRouter(prefix="/api/v1/internal/policy-debug", tags=["policy-debug"])
CurrentPrincipalDep = Annotated[Principal, Depends(get_current_principal)]


@router.get("/whoami")
async def policy_debug_whoami(
    principal: CurrentPrincipalDep,
) -> dict[str, object]:
    return {
        "organization_id": str(principal.organization_id),
        "actor_type": principal.actor_type,
        "actor_id": str(principal.user_id) if principal.user_id else None,
        "role": principal.role,
    }
