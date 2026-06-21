"""Repository interface for demo graph persistence.

The API service owns SQLAlchemy models and migrations. This lightweight repository is used
by tests and worker code that do not need to import API internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from live_demo_learner_worker.demo_graph.graph_types import DemoGraphActionEdge, DemoGraphScreenNode


@dataclass(slots=True)
class InMemoryGraphRepository:
    screens: dict[str, DemoGraphScreenNode] = field(default_factory=dict)
    edges: list[DemoGraphActionEdge] = field(default_factory=list)

    async def upsert_screen_node(
        self, node: DemoGraphScreenNode, *, organization_id: UUID | None = None
    ) -> DemoGraphScreenNode:
        self.screens[node.screen_hash] = node
        return node

    async def upsert_action_edge(
        self, edge: DemoGraphActionEdge, *, organization_id: UUID | None = None
    ) -> DemoGraphActionEdge:
        self.edges.append(edge)
        return edge

    async def get_graph_for_product(
        self,
    ) -> tuple[list[DemoGraphScreenNode], list[DemoGraphActionEdge]]:
        return list(self.screens.values()), list(self.edges)


@dataclass(slots=True)
class PostgresGraphRepository:
    sessionmaker: async_sessionmaker[AsyncSession]
    organization_id: UUID
    product_id: UUID

    async def upsert_screen_node(
        self, node: DemoGraphScreenNode, *, organization_id: UUID | None = None
    ) -> DemoGraphScreenNode:
        async with self.sessionmaker() as session, session.begin():
            existing = await session.scalar(
                text(
                    """
                    SELECT screen_id
                    FROM screen_snapshots
                    WHERE product_id = :product_id AND screen_hash = :screen_hash
                    ORDER BY created_at ASC
                    LIMIT 1
                    """
                ),
                {"product_id": node.product_id, "screen_hash": node.screen_hash},
            )
            if existing is None:
                await session.execute(
                    text(
                        """
                        INSERT INTO screen_snapshots (
                            screen_id, organization_id, product_id, url, url_path, title,
                            screen_hash, summary, confidence
                        )
                        VALUES (
                            :screen_id, :organization_id, :product_id, :url, :url_path,
                            :title, :screen_hash, :summary, :confidence
                        )
                        """
                    ),
                    {
                        "screen_id": node.screen_id,
                        "organization_id": organization_id or self.organization_id,
                        "product_id": node.product_id,
                        "url": node.url_path or "about:blank",
                        "url_path": node.url_path,
                        "title": node.title,
                        "screen_hash": node.screen_hash,
                        "summary": node.summary,
                        "confidence": node.confidence,
                    },
                )
                return node
            if existing == node.screen_id:
                await session.execute(
                    text(
                        """
                        UPDATE screen_snapshots
                        SET summary = COALESCE(:summary, summary),
                            confidence = GREATEST(confidence, :confidence)
                        WHERE screen_id = :screen_id
                        """
                    ),
                    {
                        "screen_id": node.screen_id,
                        "summary": node.summary,
                        "confidence": node.confidence,
                    },
                )
                return node
            return DemoGraphScreenNode(
                screen_id=existing,
                product_id=node.product_id,
                screen_hash=node.screen_hash,
                url_path=node.url_path,
                title=node.title,
                summary=node.summary,
                screen_type=node.screen_type,
                features=node.features,
                risk_level=node.risk_level,
                confidence=node.confidence,
            )

    async def upsert_action_edge(
        self, edge: DemoGraphActionEdge, *, organization_id: UUID | None = None
    ) -> DemoGraphActionEdge:
        async with self.sessionmaker() as session, session.begin():
            existing = (
                await session.execute(
                    text(
                        """
                        SELECT edge_id, success_count, failure_count, average_latency_ms
                        FROM demo_graph_edges
                        WHERE product_id = :product_id
                          AND from_screen_id = :from_screen_id
                          AND action_type = :action_type
                          AND COALESCE(element_fingerprint, '') = COALESCE(:element_fingerprint, '')
                        ORDER BY created_at ASC
                        LIMIT 1
                        """
                    ),
                    {
                        "product_id": edge.product_id,
                        "from_screen_id": edge.from_screen_id,
                        "action_type": edge.action_type,
                        "element_fingerprint": edge.element_fingerprint,
                    },
                )
            ).mappings().first()
            if existing is None:
                await session.execute(
                    text(
                        """
                        INSERT INTO demo_graph_edges (
                            edge_id, organization_id, product_id, from_screen_id, to_screen_id,
                            action_type, action_label, element_fingerprint, risk_level,
                            success_count, failure_count, average_latency_ms, confidence
                        )
                        VALUES (
                            :edge_id, :organization_id, :product_id, :from_screen_id,
                            :to_screen_id, :action_type, :action_label,
                            :element_fingerprint, :risk_level, :success_count,
                            :failure_count, :average_latency_ms, :confidence
                        )
                        """
                    ),
                    {
                        "edge_id": edge.edge_id,
                        "organization_id": organization_id or self.organization_id,
                        "product_id": edge.product_id,
                        "from_screen_id": edge.from_screen_id,
                        "to_screen_id": edge.to_screen_id,
                        "action_type": edge.action_type,
                        "action_label": edge.action_label,
                        "element_fingerprint": edge.element_fingerprint,
                        "risk_level": edge.risk_level,
                        "success_count": edge.success_count,
                        "failure_count": edge.failure_count,
                        "average_latency_ms": edge.average_latency_ms,
                        "confidence": edge.confidence,
                    },
                )
                return edge
            success_count = int(existing["success_count"]) + edge.success_count
            failure_count = int(existing["failure_count"]) + edge.failure_count
            sample_count = success_count + failure_count
            old_avg = existing["average_latency_ms"]
            average_latency_ms = edge.average_latency_ms
            if old_avg is not None and edge.average_latency_ms is not None and sample_count > 0:
                average_latency_ms = round(
                    float(old_avg) + (edge.average_latency_ms - float(old_avg)) / sample_count
                )
            confidence = round((success_count + 1) / (success_count + failure_count + 2), 3)
            await session.execute(
                text(
                    """
                    UPDATE demo_graph_edges
                    SET to_screen_id = COALESCE(:to_screen_id, to_screen_id),
                        action_label = COALESCE(:action_label, action_label),
                        success_count = :success_count,
                        failure_count = :failure_count,
                        average_latency_ms = :average_latency_ms,
                        confidence = :confidence,
                        updated_at = now()
                    WHERE edge_id = :edge_id
                    """
                ),
                {
                    "edge_id": existing["edge_id"],
                    "to_screen_id": edge.to_screen_id,
                    "action_label": edge.action_label,
                    "success_count": success_count,
                    "failure_count": failure_count,
                    "average_latency_ms": average_latency_ms,
                    "confidence": confidence,
                },
            )
            return edge

    async def get_graph_for_product(
        self,
    ) -> tuple[list[DemoGraphScreenNode], list[DemoGraphActionEdge]]:
        async with self.sessionmaker() as session:
            screens = (
                await session.execute(
                    text(
                        """
                        SELECT screen_id, product_id, screen_hash, url_path, title, summary,
                               confidence
                        FROM screen_snapshots
                        WHERE organization_id = :organization_id
                          AND product_id = :product_id
                        ORDER BY created_at ASC, screen_id ASC
                        LIMIT 200
                        """
                    ),
                    {"organization_id": self.organization_id, "product_id": self.product_id},
                )
            ).mappings().all()
            edges = (
                await session.execute(
                    text(
                        """
                        SELECT edge_id, product_id, from_screen_id, to_screen_id, action_type,
                               action_label, element_fingerprint, risk_level, success_count,
                               failure_count, average_latency_ms, confidence
                        FROM demo_graph_edges
                        WHERE organization_id = :organization_id
                          AND product_id = :product_id
                        ORDER BY confidence DESC, created_at ASC, edge_id ASC
                        LIMIT 1000
                        """
                    ),
                    {"organization_id": self.organization_id, "product_id": self.product_id},
                )
            ).mappings().all()
        return (
            [
                DemoGraphScreenNode(
                    screen_id=row["screen_id"],
                    product_id=row["product_id"],
                    screen_hash=row["screen_hash"],
                    url_path=row["url_path"],
                    title=row["title"],
                    summary=row["summary"],
                    screen_type=None,
                    features=(),
                    risk_level="unknown",
                    confidence=float(row["confidence"]),
                )
                for row in screens
            ],
            [
                DemoGraphActionEdge(
                    edge_id=row["edge_id"],
                    product_id=row["product_id"],
                    from_screen_id=row["from_screen_id"],
                    to_screen_id=row["to_screen_id"],
                    action_type=row["action_type"],
                    action_label=row["action_label"],
                    element_fingerprint=row["element_fingerprint"],
                    risk_level=row["risk_level"],
                    success_count=row["success_count"],
                    failure_count=row["failure_count"],
                    average_latency_ms=row["average_latency_ms"],
                    confidence=float(row["confidence"]),
                )
                for row in edges
            ],
        )
