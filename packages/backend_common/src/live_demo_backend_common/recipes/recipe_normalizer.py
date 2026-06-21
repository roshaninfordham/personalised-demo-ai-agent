from __future__ import annotations

import json
import re
import unicodedata

from live_demo_backend_common.policy.text_matching import normalize_text

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "this",
        "to",
        "with",
    }
)


def normalize_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_tokens(value: str | None) -> frozenset[str]:
    if not value:
        return frozenset()
    return frozenset(token for token in normalize_text(value).split() if token not in STOPWORDS)


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def normalized_json_size(value: object) -> int:
    return len(canonical_json(value).encode("utf-8"))


def json_depth_and_key_count(value: object) -> tuple[int, int]:
    key_count = 0

    def visit(node: object, depth: int) -> int:
        nonlocal key_count
        if isinstance(node, dict):
            key_count += len(node)
            if not node:
                return depth
            return max(visit(child, depth + 1) for child in node.values())
        if isinstance(node, list):
            if not node:
                return depth
            return max(visit(child, depth + 1) for child in node)
        return depth

    return visit(value, 0), key_count


def slug_key(value: str, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return (normalized or fallback)[:80]
