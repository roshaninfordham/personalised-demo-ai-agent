"""Deterministic context token budgeting."""

from dataclasses import dataclass
from math import ceil

from live_demo_agent_runtime.context.context_types import ContextBudgetReport


def estimate_tokens(text: str) -> int:
    return ceil(len(text) / 4)


@dataclass(frozen=True, slots=True)
class ContextSection:
    name: str
    content: str
    priority: int
    max_chars: int
    required: bool = False


@dataclass(frozen=True, slots=True)
class PackedContext:
    sections: tuple[ContextSection, ...]
    report: ContextBudgetReport


def truncate_text(value: str, max_chars: int) -> tuple[str, bool]:
    if len(value) <= max_chars:
        return value, False
    suffix = "[truncated]"
    if max_chars <= len(suffix):
        return suffix[:max_chars], True
    return value[: max(0, max_chars - len(suffix))] + suffix, True


def pack_sections(sections: list[ContextSection], max_tokens: int) -> PackedContext:
    sorted_sections = sorted(sections, key=lambda item: (item.priority, item.name))
    accepted: list[ContextSection] = []
    truncated: list[str] = []
    dropped: list[str] = []
    used_tokens = 0
    for section in sorted_sections:
        content, was_truncated = truncate_text(section.content, section.max_chars)
        candidate = ContextSection(
            name=section.name,
            content=content,
            priority=section.priority,
            max_chars=section.max_chars,
            required=section.required,
        )
        token_count = estimate_tokens(candidate.content)
        if used_tokens + token_count <= max_tokens or section.required:
            accepted.append(candidate)
            used_tokens += token_count
            if was_truncated:
                truncated.append(section.name)
        else:
            dropped.append(section.name)
    while used_tokens > max_tokens:
        optional = [item for item in accepted if not item.required]
        if not optional:
            break
        remove = max(optional, key=lambda item: (item.priority, item.name))
        accepted.remove(remove)
        dropped.append(remove.name)
        used_tokens -= estimate_tokens(remove.content)
    return PackedContext(
        sections=tuple(accepted),
        report=ContextBudgetReport(
            max_tokens=max_tokens,
            estimated_tokens=used_tokens,
            truncated_sections=tuple(sorted(set(truncated))),
            dropped_sections=tuple(sorted(set(dropped))),
        ),
    )
