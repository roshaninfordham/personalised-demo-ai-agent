from __future__ import annotations

import pytest

from live_demo_backend_common.ai.routing import HOT_PATH_WEIGHTS, compute_provider_score


def test_provider_routing_score_is_deterministic() -> None:
    score = compute_provider_score(
        normalized_latency=0.2,
        normalized_cost=0.3,
        normalized_error_rate=0.1,
        quality_score=0.9,
        weights=HOT_PATH_WEIGHTS,
    )
    assert score == pytest.approx(0.085)


def test_provider_routing_rejects_out_of_range_inputs() -> None:
    with pytest.raises(ValueError):
        compute_provider_score(1.1, 0.0, 0.0, 1.0, HOT_PATH_WEIGHTS)
