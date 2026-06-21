"""Evidence extraction helpers for summaries."""

from __future__ import annotations

import re
from collections.abc import Iterable

from live_demo_learner_worker.browser.browser_runtime_client import SafeAction, UIElement


def compact_visible_text(text: str | None, max_chars: int = 1200) -> str:
    normalized = re.sub(r"\s+", " ", (text or "")).strip()
    return normalized[:max_chars]


def heading_candidates(text: str | None, title: str | None) -> tuple[str, ...]:
    headings: list[str] = []
    if title:
        headings.append(title)
    visible = compact_visible_text(text, 500)
    for token in re.split(r"[|.\n]", visible):
        cleaned = token.strip()
        if 3 <= len(cleaned) <= 80 and cleaned[:1].isupper():
            headings.append(cleaned)
    return tuple(list(dict.fromkeys(headings))[:8])


def capability_labels(elements: Iterable[UIElement]) -> tuple[str, ...]:
    roles = {element.role or "unknown" for element in elements if element.visible}
    capabilities: list[str] = []
    if "navigation" in roles or "link" in roles:
        capabilities.append("navigation")
    if "button" in roles:
        capabilities.append("actions")
    if "textbox" in roles or "input" in roles:
        capabilities.append("forms")
    if "table" in roles or "grid" in roles:
        capabilities.append("tables")
    return tuple(capabilities)


def action_labels(actions: Iterable[SafeAction], max_items: int = 8) -> tuple[str, ...]:
    labels = list(dict.fromkeys(action.label for action in actions if action.label))
    return tuple(labels[:max_items])
