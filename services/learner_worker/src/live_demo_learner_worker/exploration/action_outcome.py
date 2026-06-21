"""Action exploration outcome types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExplorationOutcome:
    attempted: int
    skipped: int
    succeeded: int
    failed: int
    visited_screens: int
