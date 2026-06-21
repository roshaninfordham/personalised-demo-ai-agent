from __future__ import annotations

import re
import unicodedata
from typing import Any

from live_demo_backend_common.policy.policy_types import MatchedPolicyRule


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    return re.sub(r"\s+", " ", normalized).strip()


class PhraseTrie:
    def __init__(self, phrases: list[tuple[str, str, str]]) -> None:
        self.root: dict[str, Any] = {}
        self.max_phrase_len = 1
        for phrase, rule_id, category in phrases:
            tokens = normalize_text(phrase).split()
            if not tokens:
                continue
            self.max_phrase_len = max(self.max_phrase_len, len(tokens))
            node: dict[str, Any] = self.root
            for token in tokens:
                child = node.setdefault(token, {})
                if not isinstance(child, dict):
                    child = {}
                    node[token] = child
                node = child
            rules = node.setdefault("_rules", [])
            if isinstance(rules, list):
                rules.append((rule_id, category, phrase))

    def match(self, text: str) -> list[MatchedPolicyRule]:
        tokens = normalize_text(text).split()
        matches: list[MatchedPolicyRule] = []
        for index in range(len(tokens)):
            node: dict[str, Any] = self.root
            for token in tokens[index : index + self.max_phrase_len]:
                child = node.get(token)
                if not isinstance(child, dict):
                    break
                node = child
                rules = node.get("_rules")
                if isinstance(rules, list):
                    matches.extend(
                        MatchedPolicyRule(rule_id=rule_id, category=category, phrase=phrase)
                        for rule_id, category, phrase in rules
                    )
        return matches
