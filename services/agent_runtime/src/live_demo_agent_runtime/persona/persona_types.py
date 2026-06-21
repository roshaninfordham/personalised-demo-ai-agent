"""Persona state types."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class PersonaSignal:
    label: str
    confidence: float
    evidence: str


@dataclass(frozen=True, slots=True)
class PersonaState:
    likely_role: str | None
    role_confidence: float
    role_distribution: dict[str, float]
    interests: tuple[PersonaSignal, ...] = ()
    pain_points: tuple[PersonaSignal, ...] = ()
    objections: tuple[PersonaSignal, ...] = ()
    preferred_demo_direction: str | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
