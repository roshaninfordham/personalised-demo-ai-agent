"""Learner run, graph, route, and knowledge endpoints."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api import permissions
from live_demo_api.dependencies import get_db_session, get_redis_client, get_request_context
from live_demo_api.errors import NotFoundError
from live_demo_api.rbac_dependencies import require_permission
from live_demo_api.repositories.demo_routes import DemoRouteRepository
from live_demo_api.repositories.learner_jobs import LearnerRunRepository
from live_demo_api.security import Principal, RequestContext
from live_demo_api.services.learner_service import LearnerService, _serialize_run

router = APIRouter(prefix="/api/v1/products/{product_id}", tags=["learner"])
DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
RedisDep = Annotated[Any, Depends(get_redis_client)]
RequestContextDep = Annotated[RequestContext, Depends(get_request_context)]
ProductReadPrincipalDep = Annotated[
    Principal, Depends(require_permission(permissions.PRODUCT_READ))
]
ProductUpdatePrincipalDep = Annotated[
    Principal, Depends(require_permission(permissions.PRODUCT_UPDATE))
]


class CreateLearningRunRequest(BaseModel):
    trigger_type: str = Field(default="manual")
    start_url: str | None = None
    session_id: UUID | None = None


@router.post("/learning-runs")
async def create_learning_run(
    product_id: UUID,
    request: CreateLearningRunRequest,
    db: DbSessionDep,
    redis: RedisDep,
    principal: ProductUpdatePrincipalDep,
    request_context: RequestContextDep,
) -> dict[str, object]:
    return await LearnerService().create_learning_run(
        db,
        redis,
        principal,
        product_id=product_id,
        trigger_type=request.trigger_type,
        start_url=request.start_url,
        session_id=request.session_id,
        request_context=request_context,
    )


@router.get("/learning-runs")
async def list_learning_runs(
    product_id: UUID,
    db: DbSessionDep,
    principal: ProductReadPrincipalDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> dict[str, object]:
    rows = await LearnerRunRepository(db).list_runs(
        organization_id=principal.organization_id,
        product_id=product_id,
        limit=limit,
    )
    return {"items": [_serialize_run(row) for row in rows]}


@router.get("/learning-runs/{learning_run_id}")
async def get_learning_run(
    product_id: UUID,
    learning_run_id: UUID,
    db: DbSessionDep,
    principal: ProductReadPrincipalDep,
) -> dict[str, object]:
    row = await LearnerRunRepository(db).get_run(
        organization_id=principal.organization_id,
        product_id=product_id,
        learning_run_id=learning_run_id,
    )
    if row is None:
        raise NotFoundError("Learning run not found.", code="learning_run_not_found")
    return _serialize_run(row)


@router.get("/demo-graph")
async def get_demo_graph(
    product_id: UUID,
    db: DbSessionDep,
    principal: ProductReadPrincipalDep,
) -> dict[str, object]:
    return await DemoRouteRepository(db).get_demo_graph(
        organization_id=principal.organization_id,
        product_id=product_id,
    )


@router.get("/generated-routes")
async def list_generated_routes(
    product_id: UUID,
    db: DbSessionDep,
    principal: ProductReadPrincipalDep,
) -> dict[str, object]:
    rows = await DemoRouteRepository(db).list_routes(
        organization_id=principal.organization_id,
        product_id=product_id,
    )
    return {
        "items": [
            {
                "route_id": str(row.route_id),
                "route_name": row.route_name,
                "route_type": row.route_type,
                "status": row.status,
                "confidence": float(row.confidence),
                "summary": row.summary,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.post("/generated-routes/{route_id}/activate")
async def activate_generated_route(
    product_id: UUID,
    route_id: UUID,
    db: DbSessionDep,
    principal: ProductUpdatePrincipalDep,
) -> dict[str, object]:
    async with db.begin():
        route = await DemoRouteRepository(db).activate_route(
            organization_id=principal.organization_id,
            product_id=product_id,
            route_id=route_id,
        )
        if route is None:
            raise NotFoundError("Generated route not found.", code="generated_route_not_found")
    return {"route_id": str(route.route_id), "status": route.status}


@router.get("/knowledge/search")
async def search_knowledge(
    product_id: UUID,
    db: DbSessionDep,
    principal: ProductReadPrincipalDep,
    query: Annotated[str, Query(min_length=1, max_length=500)],
    top_k: Annotated[int, Query(ge=1, le=20)] = 5,
) -> dict[str, object]:
    rows = await DemoRouteRepository(db).search_knowledge(
        organization_id=principal.organization_id,
        product_id=product_id,
        query=query,
        top_k=top_k,
    )
    return {
        "items": [
            {
                "chunk_id": str(row.chunk_id),
                "source_type": row.source_type,
                "source_id": row.source_id,
                "title": row.title,
                "content": row.content,
                "metadata": row.metadata_,
                "confidence": float(row.source_confidence or 0),
            }
            for row in rows
        ]
    }
