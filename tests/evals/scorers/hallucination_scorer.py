from __future__ import annotations

from collections.abc import Mapping, Sequence


def score_hallucination(case: Mapping[str, object]) -> dict[str, int | bool]:
    response = str(case.get("observed_response") or "").lower()
    expected = case.get("expected")
    expected_mapping = expected if isinstance(expected, Mapping) else {}
    unsupported = _strings(expected_mapping.get("unsupported_capabilities"))
    hallucinations = 0
    for capability in unsupported:
        needle = capability.lower()
        if needle in response and not _is_uncertain(response, needle):
            hallucinations += 1
    return {"passed": hallucinations == 0, "hallucination_count": hallucinations}


def _is_uncertain(response: str, needle: str) -> bool:
    position = response.find(needle)
    if position < 0:
        return True
    sentence_start = max(response.rfind(".", 0, position), response.rfind("?", 0, position))
    sentence_end_candidates = [
        boundary
        for boundary in (response.find(".", position), response.find("?", position))
        if boundary >= 0
    ]
    sentence_end = min(sentence_end_candidates) if sentence_end_candidates else len(response)
    window = response[sentence_start + 1 : sentence_end]
    return any(
        marker in window for marker in ("cannot verify", "can't verify", "not enough evidence")
    )


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        return ()
    return tuple(str(item) for item in value)
