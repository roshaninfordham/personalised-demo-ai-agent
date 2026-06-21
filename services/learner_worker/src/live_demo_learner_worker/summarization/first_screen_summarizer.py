"""First-screen summary orchestrator."""

from __future__ import annotations

from live_demo_learner_worker.summarization.deterministic_screen_summarizer import (
    DeterministicScreenSummarizer,
)
from live_demo_learner_worker.summarization.llm_screen_summarizer import LlmScreenSummarizer
from live_demo_learner_worker.summarization.screen_summary_types import (
    FirstScreenSummaryInput,
    ScreenSummary,
)


class FirstScreenSummarizer:
    def __init__(self, *, use_llm: bool = False) -> None:
        self._deterministic = DeterministicScreenSummarizer()
        self._llm = LlmScreenSummarizer(self._deterministic)
        self._use_llm = use_llm

    async def summarize(self, input_data: FirstScreenSummaryInput) -> ScreenSummary:
        if self._use_llm:
            return await self._llm.summarize(input_data)
        return self._deterministic.summarize(input_data)
