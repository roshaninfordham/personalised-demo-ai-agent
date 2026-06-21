"""Graph algorithms for generated demo planning."""

from __future__ import annotations

import heapq
import math
from collections import deque
from uuid import UUID

from live_demo_learner_worker.demo_graph.graph_types import DemoGraphActionEdge, DemoGraphScreenNode


def build_adjacency(edges: list[DemoGraphActionEdge]) -> dict[UUID, list[DemoGraphActionEdge]]:
    adjacency: dict[UUID, list[DemoGraphActionEdge]] = {}
    for edge in edges:
        adjacency.setdefault(edge.from_screen_id, []).append(edge)
    for edge_list in adjacency.values():
        edge_list.sort(
            key=lambda edge: (-edge.confidence, edge.action_label or "", str(edge.edge_id))
        )
    return adjacency


def get_best_edges_from_screen(
    edges: list[DemoGraphActionEdge],
    screen_id: UUID,
    *,
    limit: int = 5,
) -> list[DemoGraphActionEdge]:
    return [
        edge
        for edge in sorted(
            edges,
            key=lambda item: (-item.confidence, item.action_label or "", str(item.edge_id)),
        )
        if edge.from_screen_id == screen_id and edge.risk_level in {"low", "medium"}
    ][:limit]


def find_shortest_safe_path(
    edges: list[DemoGraphActionEdge],
    start_screen_id: UUID,
    target_screen_id: UUID,
) -> list[DemoGraphActionEdge]:
    adjacency = build_adjacency([edge for edge in edges if edge.risk_level in {"low", "medium"}])
    queue: deque[tuple[UUID, list[DemoGraphActionEdge]]] = deque([(start_screen_id, [])])
    visited: set[UUID] = {start_screen_id}
    while queue:
        screen_id, path = queue.popleft()
        if screen_id == target_screen_id:
            return path
        for edge in adjacency.get(screen_id, []):
            if edge.to_screen_id is None or edge.to_screen_id in visited:
                continue
            visited.add(edge.to_screen_id)
            queue.append((edge.to_screen_id, [*path, edge]))
    return []


def find_highest_confidence_path(
    edges: list[DemoGraphActionEdge],
    start_screen_id: UUID,
    target_screen_id: UUID,
) -> list[DemoGraphActionEdge]:
    adjacency = build_adjacency([edge for edge in edges if edge.risk_level in {"low", "medium"}])
    heap: list[tuple[float, str, UUID, list[DemoGraphActionEdge]]] = [
        (0.0, "", start_screen_id, [])
    ]
    best_cost: dict[UUID, float] = {start_screen_id: 0.0}
    while heap:
        cost, _, screen_id, path = heapq.heappop(heap)
        if screen_id == target_screen_id:
            return path
        if cost > best_cost.get(screen_id, math.inf):
            continue
        for edge in adjacency.get(screen_id, []):
            if edge.to_screen_id is None:
                continue
            confidence = max(edge.confidence, 0.001)
            next_cost = cost - math.log(confidence)
            if next_cost < best_cost.get(edge.to_screen_id, math.inf):
                best_cost[edge.to_screen_id] = next_cost
                heapq.heappush(
                    heap,
                    (next_cost, str(edge.edge_id), edge.to_screen_id, [*path, edge]),
                )
    return []


def rank_screens_by_demo_value(nodes: list[DemoGraphScreenNode]) -> list[DemoGraphScreenNode]:
    return sorted(
        nodes, key=lambda node: (-_screen_value(node), node.title or "", str(node.screen_id))
    )


def _screen_value(node: DemoGraphScreenNode) -> float:
    screen_type_value = {
        "dashboard_or_overview": 1.0,
        "report": 0.9,
        "form": 0.8,
        "settings_or_risky": 0.2,
    }.get(node.screen_type or "", 0.4)
    risk_penalty = 0.3 if node.risk_level in {"high", "blocked"} else 0.0
    return screen_type_value + 0.2 * len(node.features) + node.confidence - risk_penalty
