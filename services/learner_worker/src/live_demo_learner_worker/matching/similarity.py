"""Deterministic similarity functions."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def cosine_similarity_sparse(counter_a: Mapping[str, int], counter_b: Mapping[str, int]) -> float:
    keys = set(counter_a) | set(counter_b)
    if not keys:
        return 1.0
    dot = sum(counter_a.get(key, 0) * counter_b.get(key, 0) for key in keys)
    norm_a = math.sqrt(sum(value * value for value in counter_a.values()))
    norm_b = math.sqrt(sum(value * value for value in counter_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def normalized_levenshtein_similarity(a: str | None, b: str | None, max_len: int = 128) -> float:
    left = (a or "")[:max_len]
    right = (b or "")[:max_len]
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    distance = _levenshtein(left, right)
    return 1 - distance / max(len(left), len(right))


def bbox_similarity(a: Mapping[str, float] | None, b: Mapping[str, float] | None) -> float:
    if a is None or b is None:
        return 0.0
    ax = a.get("x", 0.0) + a.get("width", 0.0) / 2
    ay = a.get("y", 0.0) + a.get("height", 0.0) / 2
    bx = b.get("x", 0.0) + b.get("width", 0.0) / 2
    by = b.get("y", 0.0) + b.get("height", 0.0) / 2
    diag = math.sqrt(1920 * 1920 + 1080 * 1080)
    distance = math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)
    position_score = 1 - min(1.0, distance / diag)
    area_a = max(1.0, a.get("width", 0.0) * a.get("height", 0.0))
    area_b = max(1.0, b.get("width", 0.0) * b.get("height", 0.0))
    size_ratio = min(area_a, area_b) / max(area_a, area_b)
    return 0.7 * position_score + 0.3 * size_ratio


def weighted_similarity(features: Sequence[tuple[float, float]]) -> float:
    total_weight = sum(weight for weight, _ in features)
    if total_weight == 0:
        return 0.0
    return sum(weight * value for weight, value in features) / total_weight


def token_set(text: str | None) -> set[str]:
    return {token for token in (text or "").lower().split() if token}


def token_counter(text: str | None) -> Counter[str]:
    return Counter(token_set(text))


def _levenshtein(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, 1):
        current = [i]
        for j, char_b in enumerate(b, 1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (char_a != char_b)
            current.append(min(insert, delete, replace))
        previous = current
    return previous[-1]
