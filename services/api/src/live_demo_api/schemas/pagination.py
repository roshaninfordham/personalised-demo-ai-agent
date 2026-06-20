"""API-only pagination helper schema."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    items: list[object]
    next_cursor: str | None
