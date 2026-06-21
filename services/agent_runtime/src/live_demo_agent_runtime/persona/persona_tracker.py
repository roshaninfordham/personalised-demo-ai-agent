"""Bounded deterministic persona tracker."""

from live_demo_agent_runtime.config import AgentRuntimeSettings
from live_demo_agent_runtime.context.context_types import PersonaContext
from live_demo_agent_runtime.persona.persona_scoring import (
    initial_role_distribution,
    update_role_distribution,
)
from live_demo_agent_runtime.persona.persona_signals import (
    extract_persona_signals,
    extract_role_signal_weights,
)
from live_demo_agent_runtime.persona.persona_types import PersonaSignal, PersonaState


class PersonaTracker:
    def __init__(self, settings: AgentRuntimeSettings) -> None:
        self._settings = settings

    def initial_state(self, default_role: str | None = None) -> PersonaState:
        distribution = initial_role_distribution(default_role)
        role, confidence = max(distribution.items(), key=lambda item: item[1])
        return PersonaState(
            likely_role=role,
            role_confidence=confidence,
            role_distribution=distribution,
        )

    def update(self, state: PersonaState, user_utterance: str) -> PersonaState:
        distribution = update_role_distribution(
            state.role_distribution,
            extract_role_signal_weights(user_utterance),
            decay=self._settings.persona_confidence_decay,
        )
        role, confidence = max(distribution.items(), key=lambda item: item[1])
        interests, pain_points, objections = extract_persona_signals(user_utterance)
        return PersonaState(
            likely_role=role,
            role_confidence=confidence,
            role_distribution=distribution,
            interests=_bounded_merge(
                state.interests,
                interests,
                self._settings.persona_max_interests,
            ),
            pain_points=_bounded_merge(
                state.pain_points,
                pain_points,
                self._settings.persona_max_pain_points,
            ),
            objections=_bounded_merge(
                state.objections,
                objections,
                self._settings.persona_max_objections,
            ),
            preferred_demo_direction=(
                _preferred_direction(interests) or state.preferred_demo_direction
            ),
        )

    def to_context(self, state: PersonaState) -> PersonaContext:
        if state.role_confidence < self._settings.persona_min_confidence_to_personalize:
            likely_role: str | None = None
        else:
            likely_role = state.likely_role
        return PersonaContext(
            likely_role=likely_role,
            role_confidence=state.role_confidence,
            interests=tuple(signal.label for signal in state.interests),
            pain_points=tuple(signal.label for signal in state.pain_points),
            objections=tuple(signal.label for signal in state.objections),
            preferred_demo_direction=state.preferred_demo_direction,
            evidence=tuple(signal.evidence for signal in state.interests[:3]),
        )


def _bounded_merge(
    existing: tuple[PersonaSignal, ...],
    new: tuple[PersonaSignal, ...],
    limit: int,
) -> tuple[PersonaSignal, ...]:
    by_label = {signal.label: signal for signal in existing}
    for signal in new:
        by_label[signal.label] = signal
    return tuple(sorted(by_label.values(), key=lambda item: (-item.confidence, item.label))[:limit])


def _preferred_direction(interests: tuple[PersonaSignal, ...]) -> str | None:
    if not interests:
        return None
    return interests[0].label
