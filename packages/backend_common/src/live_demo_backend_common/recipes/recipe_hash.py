from __future__ import annotations

import hashlib
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from uuid import UUID

from live_demo_backend_common.recipes.recipe_normalizer import canonical_json

VOLATILE_FIELDS = {"created_at", "updated_at", "validation_warnings"}


def recipe_hash(value: object) -> str:
    return sha256_canonical(_strip_volatile(_to_plain(value)))


def compiled_hash(value: object) -> str:
    return sha256_canonical(_strip_volatile(_to_plain(value)))


def sha256_canonical(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _to_plain(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _to_plain(asdict(value))
    if isinstance(value, dict):
        return {str(key): _to_plain(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_to_plain(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def _strip_volatile(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_volatile(child)
            for key, child in sorted(value.items())
            if key not in VOLATILE_FIELDS
        }
    if isinstance(value, list):
        return [_strip_volatile(item) for item in value]
    return value
