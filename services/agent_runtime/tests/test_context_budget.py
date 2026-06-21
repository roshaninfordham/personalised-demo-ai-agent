from live_demo_agent_runtime.context.context_budget import (
    ContextSection,
    pack_sections,
    truncate_text,
)


def test_required_sections_preserved_and_low_priority_dropped() -> None:
    packed = pack_sections(
        [
            ContextSection("safety", "a" * 200, priority=1, max_chars=200, required=True),
            ContextSection("knowledge", "b" * 200, priority=10, max_chars=200),
        ],
        max_tokens=60,
    )
    assert [section.name for section in packed.sections] == ["safety"]
    assert packed.report.dropped_sections == ("knowledge",)


def test_truncation_is_deterministic() -> None:
    left, was_truncated = truncate_text("abcdef", 4)
    right, _ = truncate_text("abcdef", 4)
    assert left == right == "[truncated]"[:4]
    assert was_truncated is True
