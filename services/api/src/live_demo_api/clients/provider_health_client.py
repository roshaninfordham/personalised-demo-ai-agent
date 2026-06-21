"""Provider health client for low-cost warmup checks."""

from __future__ import annotations


class ProviderHealthClient:
    async def warm_text_provider(self, *, trace_id: str) -> bool:
        _ = trace_id
        return True

    async def warm_stt_provider(self, *, trace_id: str) -> bool:
        _ = trace_id
        return True

    async def warm_tts_provider(self, *, trace_id: str) -> bool:
        _ = trace_id
        return True

    async def warm_all(self, *, trace_id: str) -> tuple[int, tuple[str, ...]]:
        results = (
            await self.warm_text_provider(trace_id=trace_id),
            await self.warm_stt_provider(trace_id=trace_id),
            await self.warm_tts_provider(trace_id=trace_id),
        )
        failures = tuple(
            name
            for name, ok in zip(
                ("llm_unavailable", "stt_unavailable", "tts_unavailable"),
                results,
                strict=True,
            )
            if not ok
        )
        return sum(1 for item in results if item), failures
