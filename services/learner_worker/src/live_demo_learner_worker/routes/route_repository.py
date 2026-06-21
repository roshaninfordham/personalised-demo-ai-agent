"""In-memory generated route repository for worker tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from live_demo_learner_worker.routes.route_types import GeneratedDemoRoute


@dataclass(slots=True)
class InMemoryRouteRepository:
    routes: dict[UUID, GeneratedDemoRoute] = field(default_factory=dict)

    async def save_route(
        self, route: GeneratedDemoRoute, *, organization_id: UUID | None = None
    ) -> GeneratedDemoRoute:
        self.routes[route.route_id] = route
        return route

    async def list_routes(self, product_id: UUID) -> list[GeneratedDemoRoute]:
        return [route for route in self.routes.values() if route.product_id == product_id]


@dataclass(slots=True)
class PostgresRouteRepository:
    sessionmaker: async_sessionmaker[AsyncSession]
    organization_id: UUID
    learning_run_id: UUID | None = None

    async def save_route(
        self, route: GeneratedDemoRoute, *, organization_id: UUID | None = None
    ) -> GeneratedDemoRoute:
        org_id = organization_id or self.organization_id
        async with self.sessionmaker() as session, session.begin():
            await session.execute(
                text(
                    """
                    INSERT INTO generated_demo_routes (
                        route_id, organization_id, product_id, learning_run_id, route_name,
                        route_type, status, confidence, summary
                    )
                    VALUES (
                        :route_id, :organization_id, :product_id, :learning_run_id,
                        :route_name, :route_type, :status, :confidence, :summary
                    )
                    ON CONFLICT (route_id) DO UPDATE SET
                        route_name = EXCLUDED.route_name,
                        status = EXCLUDED.status,
                        confidence = EXCLUDED.confidence,
                        summary = EXCLUDED.summary,
                        updated_at = now()
                    """
                ),
                {
                    "route_id": route.route_id,
                    "organization_id": org_id,
                    "product_id": route.product_id,
                    "learning_run_id": self.learning_run_id,
                    "route_name": route.route_name,
                    "route_type": route.route_type,
                    "status": route.status,
                    "confidence": route.confidence,
                    "summary": route.summary,
                },
            )
            for step in route.steps:
                await session.execute(
                    text(
                        """
                        INSERT INTO generated_demo_route_steps (
                            route_step_id, route_id, organization_id, step_order, step_key,
                            phase, goal, screen_id, recommended_action_id,
                            recommended_action_label, talk_track, fallback_strategy,
                            confidence, evidence
                        )
                        VALUES (
                            :route_step_id, :route_id, :organization_id, :step_order,
                            :step_key, :phase, :goal, :screen_id, :recommended_action_id,
                            :recommended_action_label, :talk_track, :fallback_strategy,
                            :confidence, CAST(:evidence AS jsonb)
                        )
                        ON CONFLICT (route_id, step_order) DO UPDATE SET
                            step_key = EXCLUDED.step_key,
                            phase = EXCLUDED.phase,
                            goal = EXCLUDED.goal,
                            screen_id = EXCLUDED.screen_id,
                            recommended_action_id = EXCLUDED.recommended_action_id,
                            recommended_action_label = EXCLUDED.recommended_action_label,
                            talk_track = EXCLUDED.talk_track,
                            fallback_strategy = EXCLUDED.fallback_strategy,
                            confidence = EXCLUDED.confidence,
                            evidence = EXCLUDED.evidence,
                            updated_at = now()
                        """
                    ),
                    {
                        "route_step_id": step.route_step_id,
                        "route_id": route.route_id,
                        "organization_id": org_id,
                        "step_order": step.step_order,
                        "step_key": step.step_key,
                        "phase": step.phase,
                        "goal": step.goal,
                        "screen_id": step.screen_id,
                        "recommended_action_id": step.recommended_action_id,
                        "recommended_action_label": step.recommended_action_label,
                        "talk_track": step.talk_track,
                        "fallback_strategy": step.fallback_strategy,
                        "confidence": step.confidence,
                        "evidence": _json(step.evidence),
                    },
                )
        return route

    async def list_routes(self, product_id: UUID) -> list[GeneratedDemoRoute]:
        return []


def _json(value: object) -> str:
    import json

    return json.dumps(value, sort_keys=True, default=str)
