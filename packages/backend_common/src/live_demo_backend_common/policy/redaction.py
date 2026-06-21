from __future__ import annotations

import hashlib
import hmac
import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from live_demo_backend_common.policy.policy_types import RedactionFinding, RedactionResult
from live_demo_backend_common.policy.redaction_patterns import (
    SAFE_PATTERNS,
    SENSITIVE_KEYS,
    looks_like_high_entropy_secret,
    luhn_valid,
)
from live_demo_backend_common.policy.text_matching import PhraseTrie, normalize_text


class RedactionContext(StrEnum):
    LOG = "log"
    PROMPT = "prompt"
    AUDIT = "audit"
    SCREEN_SUMMARY = "screen_summary"
    SCREENSHOT_METADATA = "screenshot_metadata"
    LEAD_SUMMARY = "lead_summary"
    CRM_PAYLOAD = "crm_payload"
    KNOWLEDGE_CHUNK = "knowledge_chunk"


@dataclass(frozen=True, slots=True)
class RedactionConfig:
    hash_secret: str | None = None
    customer_name_list: tuple[str, ...] = ()
    max_text_chars: int = 100_000
    max_json_depth: int = 10
    max_json_keys: int = 5000


class RedactionEngine:
    def __init__(self, config: RedactionConfig | None = None) -> None:
        self._config = config or RedactionConfig()
        self._customer_matcher = PhraseTrie(
            [(name, "customer_name", "customer_name") for name in self._config.customer_name_list]
        )

    def redact_text(self, text: str, context: RedactionContext) -> RedactionResult:
        original = text[: self._config.max_text_chars]
        findings: list[RedactionFinding] = []
        redacted = original
        for finding_type, pattern, replacement in SAFE_PATTERNS:
            redacted, count = pattern.subn(replacement, redacted)
            if count:
                findings.append(RedactionFinding(finding_type, "mask"))
        redacted, cc_count = _redact_credit_cards(redacted)
        if cc_count:
            findings.append(RedactionFinding("credit_card", "mask"))
        for match in self._customer_matcher.match(redacted):
            if match.phrase:
                redacted = re.sub(
                    re.escape(match.phrase),
                    "[REDACTED_CUSTOMER_NAME]",
                    redacted,
                    flags=re.IGNORECASE,
                )
                findings.append(RedactionFinding("customer_name", "mask"))
        if not findings and looks_like_high_entropy_secret(redacted) and context in {
            RedactionContext.LOG,
            RedactionContext.PROMPT,
        }:
            redacted = "[REDACTED_SECRET]"
            findings.append(RedactionFinding("high_entropy_secret", "mask"))
        return RedactionResult(
            redacted_value=redacted,
            applied=bool(findings),
            findings=tuple(findings),
            original_hash=_hash_value(original),
        )

    def redact_json(self, value: Any, context: RedactionContext) -> RedactionResult:
        findings: list[RedactionFinding] = []
        key_count = 0

        def visit(node: Any, path: str, depth: int) -> Any:
            nonlocal key_count
            if depth > self._config.max_json_depth:
                findings.append(RedactionFinding("redaction_input_too_deep", "drop", path))
                return "[REDACTED_TOO_DEEP]"
            if isinstance(node, Mapping):
                output: dict[str, Any] = {}
                key_count += len(node)
                if key_count > self._config.max_json_keys:
                    findings.append(RedactionFinding("redaction_input_too_large", "drop", path))
                    return {"redacted": "[REDACTED_TOO_LARGE]"}
                for key, child in node.items():
                    normalized_key = normalize_text(str(key)).replace(" ", "_")
                    child_path = f"{path}.{key}"
                    if _sensitive_key(normalized_key):
                        output[str(key)] = "[REDACTED_SECRET]"
                        findings.append(RedactionFinding("sensitive_key", "mask", child_path))
                    else:
                        output[str(key)] = visit(child, child_path, depth + 1)
                return output
            if isinstance(node, list):
                return [
                    visit(item, f"{path}[{index}]", depth + 1)
                    for index, item in enumerate(node)
                ]
            if isinstance(node, str):
                result = self.redact_text(node, context)
                findings.extend(
                    RedactionFinding(
                        item.finding_type,
                        item.redaction_mode,
                        path,
                        item.start,
                        item.end,
                        item.confidence,
                    )
                    for item in result.findings
                )
                return result.redacted_value
            return node

        redacted = visit(value, "$", 0)
        return RedactionResult(
            redacted_value=redacted,
            applied=bool(findings),
            findings=tuple(findings),
            original_hash=_hash_value(repr(value)),
        )

    def redact_mapping_keys(
        self,
        mapping: Mapping[str, Any],
        context: RedactionContext,
    ) -> RedactionResult:
        return self.redact_json(dict(mapping), context)

    def pseudonymize(self, finding_type: str, value: str) -> str:
        if not self._config.hash_secret:
            return f"[REDACTED_{finding_type.upper()}]"
        digest = hmac.new(
            self._config.hash_secret.encode(),
            value.lower().strip().encode(),
            "sha256",
        ).hexdigest()[:8]
        return f"[{finding_type.upper()}:{digest}]"


def screenshot_metadata_redaction_metadata(result: RedactionResult) -> dict[str, object]:
    return {
        "contains_potential_sensitive_visual_data": result.applied,
        "text_metadata_redacted": result.applied,
        "visual_redaction_applied": False,
    }


def _sensitive_key(normalized_key: str) -> bool:
    return normalized_key in SENSITIVE_KEYS or any(key in normalized_key for key in SENSITIVE_KEYS)


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _redact_credit_cards(text: str) -> tuple[str, int]:
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        value = match.group(0)
        if luhn_valid(value):
            count += 1
            return "[REDACTED_CREDIT_CARD]"
        return value

    return re.sub(r"\b(?:\d[ -]?){13,19}\b", replace, text), count
