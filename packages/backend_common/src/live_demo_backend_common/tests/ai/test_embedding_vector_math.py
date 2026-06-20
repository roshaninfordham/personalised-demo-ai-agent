from __future__ import annotations

import math

import pytest

from live_demo_backend_common.ai.embeddings.vector_math import (
    cosine_similarity,
    l2_norm,
    normalize_l2,
    validate_vector_dimensions,
)


def test_l2_normalization_and_cosine_similarity() -> None:
    normalized = normalize_l2([3.0, 4.0])
    assert math.isclose(l2_norm(normalized), 1.0)
    assert math.isclose(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
    assert math.isclose(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)


def test_vector_validation_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        normalize_l2([0.0, 0.0])
    with pytest.raises(ValueError):
        l2_norm([math.nan])
    with pytest.raises(ValueError):
        validate_vector_dimensions([1.0], 2)
