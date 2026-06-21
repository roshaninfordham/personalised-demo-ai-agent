"""Exploration limit configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExplorationLimits:
    max_pages_per_product: int = 20
    max_depth: int = 2
    max_actions_per_screen: int = 8
    max_total_actions: int = 50
    max_recovery_attempts: int = 2
