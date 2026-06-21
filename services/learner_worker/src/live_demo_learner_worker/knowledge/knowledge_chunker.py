"""Deterministic paragraph-aware knowledge chunker."""

from __future__ import annotations

import re

from live_demo_backend_common.policy.redaction import RedactionContext, RedactionEngine
from live_demo_learner_worker.knowledge.chunk_types import (
    KnowledgeChunk,
    KnowledgeChunkInput,
    make_chunk,
)


class KnowledgeChunker:
    def __init__(
        self,
        redaction_engine: RedactionEngine,
        *,
        max_chars: int = 1200,
        overlap_chars: int = 150,
        min_chars: int = 150,
    ) -> None:
        self._redaction_engine = redaction_engine
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars
        self._min_chars = min_chars

    def chunk(self, input_data: KnowledgeChunkInput) -> tuple[KnowledgeChunk, ...]:
        redacted = self._redaction_engine.redact_text(
            input_data.content, RedactionContext.KNOWLEDGE_CHUNK
        )
        content = normalize_whitespace(str(redacted.redacted_value))
        if not content:
            return ()
        if _secret_heavy(input_data.content, content):
            return ()
        chunks = _split_content(content, self._max_chars, self._overlap_chars, self._min_chars)
        return tuple(
            make_chunk(input_data, content=chunk, redaction_applied=redacted.applied)
            for chunk in chunks
        )


def normalize_whitespace(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip()


def _split_content(
    content: str,
    max_chars: int,
    overlap_chars: int,
    min_chars: int,
) -> list[str]:
    paragraphs = [
        paragraph.strip() for paragraph in re.split(r"\n{2,}", content) if paragraph.strip()
    ]
    if not paragraphs:
        paragraphs = [content]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        units = _split_long_paragraph(paragraph, max_chars)
        for unit in units:
            if len(current) + len(unit) + 1 <= max_chars:
                current = f"{current} {unit}".strip()
                continue
            if current:
                chunks.append(current)
            current = (
                _overlap_tail(chunks[-1], overlap_chars) + " " + unit
                if chunks and overlap_chars
                else unit
            )
            current = current.strip()[:max_chars]
    if current:
        chunks.append(current)
    filtered = [chunk for chunk in chunks if len(chunk) >= min_chars]
    if not filtered and chunks:
        return [chunks[0]]
    return filtered


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]
    sentences = [
        sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", paragraph) if sentence.strip()
    ]
    output: list[str] = []
    for sentence in sentences:
        if len(sentence) <= max_chars:
            output.append(sentence)
        else:
            output.extend(
                sentence[index : index + max_chars] for index in range(0, len(sentence), max_chars)
            )
    return output


def _overlap_tail(chunk: str, overlap_chars: int) -> str:
    return chunk[-overlap_chars:].strip()


def _secret_heavy(original: str, redacted: str) -> bool:
    if not original:
        return False
    redacted_chars = max(0, len(original) - len(redacted.replace("[REDACTED_SECRET]", "")))
    return redacted_chars / len(original) > 0.40
