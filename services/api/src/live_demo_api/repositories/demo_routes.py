"""Generated demo route and graph repositories."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from live_demo_api.db.models import (
    DemoGraphEdge,
    GeneratedDemoRoute,
    KnowledgeChunk,
    ScreenSnapshot,
)


class DemoRouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_routes(
        self, *, organization_id: UUID, product_id: UUID
    ) -> list[GeneratedDemoRoute]:
        return list(
            (
                await self._session.scalars(
                    sa.select(GeneratedDemoRoute)
                    .where(
                        GeneratedDemoRoute.organization_id == organization_id,
                        GeneratedDemoRoute.product_id == product_id,
                        GeneratedDemoRoute.deleted_at.is_(None),
                    )
                    .order_by(
                        GeneratedDemoRoute.confidence.desc(), GeneratedDemoRoute.created_at.desc()
                    )
                )
            ).all()
        )

    async def activate_route(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        route_id: UUID,
    ) -> GeneratedDemoRoute | None:
        route = cast(
            GeneratedDemoRoute | None,
            await self._session.scalar(
                sa.select(GeneratedDemoRoute).where(
                    GeneratedDemoRoute.organization_id == organization_id,
                    GeneratedDemoRoute.product_id == product_id,
                    GeneratedDemoRoute.route_id == route_id,
                    GeneratedDemoRoute.deleted_at.is_(None),
                )
            ),
        )
        if route is None:
            return None
        await self._session.execute(
            sa.update(GeneratedDemoRoute)
            .where(
                GeneratedDemoRoute.organization_id == organization_id,
                GeneratedDemoRoute.product_id == product_id,
                GeneratedDemoRoute.status == "active",
            )
            .values(status="archived", updated_at=datetime.now(UTC))
        )
        route.status = "active"
        route.updated_at = datetime.now(UTC)
        await self._session.flush()
        return route

    async def get_demo_graph(self, *, organization_id: UUID, product_id: UUID) -> dict[str, object]:
        screens = list(
            (
                await self._session.scalars(
                    sa.select(ScreenSnapshot)
                    .where(
                        ScreenSnapshot.organization_id == organization_id,
                        ScreenSnapshot.product_id == product_id,
                    )
                    .order_by(ScreenSnapshot.created_at.desc())
                    .limit(200)
                )
            ).all()
        )
        edges = list(
            (
                await self._session.scalars(
                    sa.select(DemoGraphEdge)
                    .where(
                        DemoGraphEdge.organization_id == organization_id,
                        DemoGraphEdge.product_id == product_id,
                    )
                    .order_by(DemoGraphEdge.confidence.desc())
                    .limit(1000)
                )
            ).all()
        )
        return {
            "screens": [
                {
                    "screen_id": str(screen.screen_id),
                    "screen_hash": screen.screen_hash,
                    "url_path": screen.url_path,
                    "title": screen.title,
                    "summary": screen.summary,
                    "confidence": float(screen.confidence),
                }
                for screen in screens
            ],
            "edges": [
                {
                    "edge_id": str(edge.edge_id),
                    "from_screen_id": str(edge.from_screen_id) if edge.from_screen_id else None,
                    "to_screen_id": str(edge.to_screen_id) if edge.to_screen_id else None,
                    "action_type": edge.action_type,
                    "action_label": edge.action_label,
                    "risk_level": edge.risk_level,
                    "confidence": float(edge.confidence),
                }
                for edge in edges
            ],
        }

    async def search_knowledge(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        query: str,
        top_k: int,
    ) -> list[KnowledgeChunk]:
        terms = [term for term in query.lower().split() if term]
        statement = sa.select(KnowledgeChunk).where(
            KnowledgeChunk.organization_id == organization_id,
            KnowledgeChunk.product_id == product_id,
            KnowledgeChunk.deleted_at.is_(None),
        )
        if terms:
            statement = statement.where(
                sa.or_(*(sa.func.lower(KnowledgeChunk.content).contains(term) for term in terms))
            )
        statement = statement.order_by(KnowledgeChunk.created_at.desc()).limit(top_k)
        return list((await self._session.scalars(statement)).all())
