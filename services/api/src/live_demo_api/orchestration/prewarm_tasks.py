"""Result containers for prewarm tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BrowserPrewarmResult:
    browser_session_id: UUID
    screen: dict[str, object]
    safe_actions: tuple[dict[str, object], ...]


@dataclass(frozen=True, slots=True)
class VoicePrewarmResult:
    voice_session_id: UUID
    join_config: dict[str, object]


@dataclass(frozen=True, slots=True)
class ProviderWarmupResult:
    warmed_count: int = 0
    required_count: int = 3
    degraded_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PrewarmTaskResults:
    browser: BrowserPrewarmResult | None = None
    voice: VoicePrewarmResult | None = None
    provider: ProviderWarmupResult = field(default_factory=ProviderWarmupResult)
    learner_run_id: UUID | None = None
    compiled_recipe_id: UUID | None = None
