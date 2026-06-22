from __future__ import annotations

from collections.abc import Mapping


def score_recipe_completion(case: Mapping[str, object]) -> dict[str, float | bool]:
    expected = case.get("expected")
    expected_mapping = expected if isinstance(expected, Mapping) else {}
    total = _float(expected_mapping.get("required_steps_total"))
    completed = _float(expected_mapping.get("required_steps_completed"))
    score = completed / total if total > 0 else 1.0
    return {"passed": score >= 0.8, "recipe_completion_score": score}


def _float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    return 0.0
