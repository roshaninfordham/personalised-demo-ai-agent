"""Optional LLM screen summarizer adapter.

The deterministic summarizer remains the trusted fallback; this adapter is intentionally
conservative so invalid or unsupported LLM output cannot block the learner.
"""

from __future__ import annotations

from live_demo_learner_worker.summarization.deterministic_screen_summarizer import (
    DeterministicScreenSummarizer,
)
from live_demo_learner_worker.summarization.screen_summary_types import (
    FirstScreenSummaryInput,
    ScreenSummary,
)


class LlmScreenSummarizer:
    def __init__(self, fallback: DeterministicScreenSummarizer | None = None) -> None:
        self._fallback = fallback or DeterministicScreenSummarizer()

    async def summarize(self, input_data: FirstScreenSummaryInput) -> ScreenSummary:
        return self._fallback.summarize(input_data)
