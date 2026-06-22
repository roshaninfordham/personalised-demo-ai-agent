from __future__ import annotations

from collections.abc import Mapping, Sequence


def score_grounding(case: Mapping[str, object]) -> dict[str, float | int | bool]:
    response = str(case.get("observed_response") or "").lower()
    evidence_terms = _strings(case.get("evidence_terms"))
    expected = _mapping(case.get("expected"))
    must_not = _strings(expected.get("must_not_include"))
    unsupported = sum(1 for term in must_not if term.lower() in response)
    grounded = sum(1 for term in evidence_terms if term.lower() in response)
    total = max(1, len(evidence_terms))
    score = grounded / total
    return {
        "passed": score >= 0.95 and unsupported == 0,
        "grounding_score": score,
        "unsupported_claims": unsupported,
    }


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return ()
    return tuple(str(item) for item in value)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}
