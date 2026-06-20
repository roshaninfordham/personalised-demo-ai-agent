from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProviderPurpose(StrEnum):
    realtime_host = "realtime_host"
    screen_summary = "screen_summary"
    recipe_generation = "recipe_generation"
    lead_summary = "lead_summary"
    embedding = "embedding"
    vision_fallback = "vision_fallback"
    safety_classification = "safety_classification"


@dataclass(frozen=True, slots=True)
class ProviderRoutingWeights:
    latency: float
    cost: float
    error_rate: float
    quality: float


HOT_PATH_WEIGHTS = ProviderRoutingWeights(latency=0.45, cost=0.20, error_rate=0.25, quality=0.10)
COLD_PATH_WEIGHTS = ProviderRoutingWeights(latency=0.20, cost=0.20, error_rate=0.20, quality=0.40)


def compute_provider_score(
    normalized_latency: float,
    normalized_cost: float,
    normalized_error_rate: float,
    quality_score: float,
    weights: ProviderRoutingWeights,
) -> float:
    for value in [
        normalized_latency,
        normalized_cost,
        normalized_error_rate,
        quality_score,
    ]:
        if value < 0.0 or value > 1.0:
            raise ValueError("Provider routing inputs must be in [0, 1].")
    return (
        weights.latency * normalized_latency
        + weights.cost * normalized_cost
        + weights.error_rate * normalized_error_rate
        - weights.quality * quality_score
    )
