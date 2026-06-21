"""Persona role scoring."""

from live_demo_agent_runtime.persona.persona_signals import ROLES

EPSILON = 1e-6


def initial_role_distribution(default_role: str | None = None) -> dict[str, float]:
    if default_role in ROLES:
        base = {role: 0.05 for role in ROLES}
        base[default_role] = 0.5
        return normalize_distribution(base)
    probability = 1.0 / len(ROLES)
    return {role: probability for role in ROLES}


def normalize_distribution(scores: dict[str, float]) -> dict[str, float]:
    clipped = {role: max(EPSILON, score) for role, score in scores.items()}
    total = sum(clipped.values())
    return {role: score / total for role, score in clipped.items()}


def update_role_distribution(
    prior: dict[str, float],
    signal_weights: dict[str, float],
    *,
    decay: float,
) -> dict[str, float]:
    scores = {
        role: max(EPSILON, prior.get(role, EPSILON)) ** decay
        * (1.0 + signal_weights.get(role, 0.0))
        for role in ROLES
    }
    return normalize_distribution(scores)
