"""Priority frontier for deterministic action exploration."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field


@dataclass(order=True, frozen=True, slots=True)
class ExplorationCandidate:
    priority: float
    screen_id: str = field(compare=True)
    action_id: str = field(compare=True)
    depth: int = field(compare=True)
    path: tuple[str, ...] = field(compare=True)
    score: float = field(compare=False)


class ExplorationFrontier:
    def __init__(self) -> None:
        self._heap: list[ExplorationCandidate] = []

    def push(
        self, *, screen_id: str, action_id: str, depth: int, path: tuple[str, ...], score: float
    ) -> None:
        heapq.heappush(
            self._heap,
            ExplorationCandidate(
                priority=-score,
                screen_id=screen_id,
                action_id=action_id,
                depth=depth,
                path=path,
                score=score,
            ),
        )

    def pop(self) -> ExplorationCandidate | None:
        if not self._heap:
            return None
        return heapq.heappop(self._heap)

    def __len__(self) -> int:
        return len(self._heap)
