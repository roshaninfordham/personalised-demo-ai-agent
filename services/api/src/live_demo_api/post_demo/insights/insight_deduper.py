"""Insight deduplication."""

from __future__ import annotations

from live_demo_api.post_demo.insights.insight_types import ExtractedLeadInsight, token_set


def dedupe_insights(
    insights: tuple[ExtractedLeadInsight, ...], *, threshold: float = 0.88
) -> tuple[ExtractedLeadInsight, ...]:
    merged: list[ExtractedLeadInsight] = []
    for insight in insights:
        for index, existing in enumerate(merged):
            if existing.insight_type != insight.insight_type:
                continue
            if _jaccard(existing.content, insight.content) < threshold:
                continue
            merged[index] = _merge(existing, insight)
            break
        else:
            merged.append(insight)
    return tuple(
        sorted(
            merged,
            key=lambda item: (
                -item.importance,
                -item.confidence,
                -(
                    len(item.evidence_transcript_event_ids)
                    + len(item.evidence_browser_action_ids)
                    + len(item.evidence_screen_ids)
                    + len(item.evidence_recipe_step_ids)
                ),
                item.content,
            ),
        )
    )


def _jaccard(left: str, right: str) -> float:
    left_tokens = token_set(left)
    right_tokens = token_set(right)
    if not left_tokens and not right_tokens:
        return 1.0
    return len(left_tokens & right_tokens) / max(1, len(left_tokens | right_tokens))


def _merge(left: ExtractedLeadInsight, right: ExtractedLeadInsight) -> ExtractedLeadInsight:
    content = left.content if len(left.content) >= len(right.content) else right.content
    return ExtractedLeadInsight(
        insight_type=left.insight_type,
        content=content,
        normalized_content=left.normalized_content,
        confidence=max(left.confidence, right.confidence),
        importance=max(left.importance, right.importance),
        evidence_transcript_event_ids=tuple(
            sorted(
                set(left.evidence_transcript_event_ids) | set(right.evidence_transcript_event_ids)
            )
        ),
        evidence_browser_action_ids=tuple(
            sorted(set(left.evidence_browser_action_ids) | set(right.evidence_browser_action_ids))
        ),
        evidence_screen_ids=tuple(
            sorted(set(left.evidence_screen_ids) | set(right.evidence_screen_ids))
        ),
        evidence_recipe_step_ids=tuple(
            sorted(set(left.evidence_recipe_step_ids) | set(right.evidence_recipe_step_ids))
        ),
        extraction_method=left.extraction_method,
        reason=left.reason,
    )
