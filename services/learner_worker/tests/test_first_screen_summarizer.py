from __future__ import annotations

from uuid import uuid4

import pytest

from live_demo_learner_worker.browser.browser_runtime_client import make_fixture_screen
from live_demo_learner_worker.summarization.first_screen_summarizer import FirstScreenSummarizer
from live_demo_learner_worker.summarization.screen_summary_types import FirstScreenSummaryInput


@pytest.mark.asyncio
async def test_deterministic_summary_includes_only_extracted_facts() -> None:
    screen = make_fixture_screen()
    summary = await FirstScreenSummarizer(use_llm=False).summarize(
        FirstScreenSummaryInput(
            organization_id=screen.screen_state.organization_id,
            product_id=screen.screen_state.product_id,
            session_id=None,
            screen_state=screen.screen_state,
            ui_elements=screen.ui_elements,
            visible_text=screen.screen_state.visible_text,
            safe_actions=screen.safe_actions,
            screenshot_artifact_id=None,
            trace_id="trace",
        )
    )

    assert "Dashboard" in summary.summary
    assert "Add Metric" in summary.summary
    assert summary.confidence > 0.7


@pytest.mark.asyncio
async def test_empty_screen_low_confidence() -> None:
    screen = make_fixture_screen(title="", visible_text="", screen_hash="empty")
    summary = await FirstScreenSummarizer().summarize(
        FirstScreenSummaryInput(
            organization_id=uuid4(),
            product_id=screen.screen_state.product_id,
            session_id=None,
            screen_state=screen.screen_state,
            ui_elements=(),
            visible_text=None,
            safe_actions=(),
            screenshot_artifact_id=None,
            trace_id="trace",
        )
    )

    assert summary.confidence < 0.5
    assert "visible screen text" in summary.unknowns
