from __future__ import annotations

import math
import re
from typing import cast

from live_demo_policies.redaction_rules import REDACTION_RULES

_PATTERNS = cast(list[dict[str, object]], REDACTION_RULES["patterns"])
_SENSITIVE_KEYS = cast(list[str], REDACTION_RULES["sensitive_keys"])

SAFE_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = tuple(
    (
        str(pattern["finding_type"]),
        re.compile(str(pattern["regex"]), re.IGNORECASE),
        str(pattern["replacement"]),
    )
    for pattern in _PATTERNS
)

SENSITIVE_KEYS = frozenset(str(key).lower() for key in _SENSITIVE_KEYS)


def looks_like_high_entropy_secret(value: str) -> bool:
    if len(value) < 24:
        return False
    entropy = _entropy(value)
    mixed = bool(re.search(r"[A-Z]", value) and re.search(r"[a-z]", value))
    symbols = bool(re.search(r"[0-9_\-+/=]", value))
    return entropy >= 3.5 and (mixed or symbols)


def luhn_valid(value: str) -> bool:
    digits = [int(char) for char in re.sub(r"\D", "", value)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _entropy(value: str) -> float:
    total = len(value)
    counts = {char: value.count(char) for char in set(value)}
    return -sum((count / total) * math.log2(count / total) for count in counts.values())
