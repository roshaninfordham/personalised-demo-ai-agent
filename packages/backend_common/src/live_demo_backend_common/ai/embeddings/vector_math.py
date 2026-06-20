from __future__ import annotations

import math
from collections.abc import Sequence

from live_demo_backend_common.ai.errors import ProviderResponseValidationError

EPSILON = 1e-12


def l2_norm(vector: Sequence[float]) -> float:
    _validate_finite(vector)
    return math.sqrt(sum(item * item for item in vector))


def normalize_l2(vector: Sequence[float]) -> list[float]:
    norm = l2_norm(vector)
    if norm <= EPSILON:
        raise ValueError("Cannot normalize a zero vector.")
    return [item / norm for item in vector]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    validate_vector_dimensions(a, len(b))
    denominator = l2_norm(a) * l2_norm(b)
    if denominator <= EPSILON:
        raise ValueError("Cannot compute cosine similarity with a zero vector.")
    return sum(left * right for left, right in zip(a, b, strict=True)) / denominator


def validate_vector_dimensions(vector: Sequence[float], expected: int) -> None:
    if len(vector) != expected:
        raise ValueError(f"Expected vector dimension {expected}, got {len(vector)}.")


def provider_validate_vector_dimensions(
    *,
    provider_name: str,
    model_name: str,
    operation: str,
    vector: Sequence[float],
    expected: int,
) -> None:
    try:
        validate_vector_dimensions(vector, expected)
        _validate_finite(vector)
    except ValueError as exc:
        raise ProviderResponseValidationError(
            provider_name=provider_name,
            model_name=model_name,
            operation=operation,
            retryable=False,
            status_code=None,
            safe_message="Provider returned an invalid embedding vector.",
            internal_message=str(exc),
        ) from exc


def _validate_finite(vector: Sequence[float]) -> None:
    if any(not math.isfinite(item) for item in vector):
        raise ValueError("Vector contains NaN or infinite values.")
