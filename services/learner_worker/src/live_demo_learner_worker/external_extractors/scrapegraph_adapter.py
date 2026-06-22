"""Optional ScrapeGraphAI cold-path extractor.

This adapter is deliberately not used by the realtime agent path. It is import
guarded so default installs do not require ScrapeGraphAI or its dependencies.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from live_demo_learner_worker.config import LearnerWorkerSettings
from live_demo_learner_worker.redaction.learner_redaction import LearnerRedactor


@dataclass(frozen=True)
class ScrapeGraphExtractionRequest:
    url: str
    prompt: str
    trace_id: str


@dataclass(frozen=True)
class ScrapeGraphExtractionResult:
    url: str
    extracted: dict[str, Any]
    redacted_text: str
    source: str = "scrapegraphai"
    trusted: bool = False


class ScrapeGraphUnavailableError(RuntimeError):
    """Raised when the optional ScrapeGraphAI dependency is not installed."""


class ScrapeGraphPolicyError(ValueError):
    """Raised when a URL or request violates learner extraction policy."""


class ScrapeGraphAdapter:
    """Cold-path public-page extraction adapter.

    Output is untrusted. Callers must validate and compare it with deterministic
    learner evidence before storing product facts or embeddings.
    """

    def __init__(self, settings: LearnerWorkerSettings, redactor: LearnerRedactor) -> None:
        self._settings = settings
        self._redactor = redactor

    async def extract_public_facts(
        self,
        request: ScrapeGraphExtractionRequest,
    ) -> ScrapeGraphExtractionResult | None:
        if not self._settings.scrapegraph_enabled:
            return None
        self._validate_public_url(request.url)
        raw = await asyncio.wait_for(
            asyncio.to_thread(self._run_scrapegraph, request.url, request.prompt),
            timeout=self._settings.scrapegraph_timeout_ms / 1000,
        )
        redacted = self._redactor.redact_for_embedding(str(raw))
        extracted = raw if isinstance(raw, dict) else {"content": str(raw)}
        return ScrapeGraphExtractionResult(
            url=request.url,
            extracted=extracted,
            redacted_text=str(redacted.redacted_value),
        )

    def _run_scrapegraph(self, url: str, prompt: str) -> Any:
        try:
            from scrapegraphai.graphs import SmartScraperGraph  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ScrapeGraphUnavailableError(
                "ScrapeGraphAI is not installed. Start the scrapegraph profile to enable it."
            ) from exc

        graph_config = {
            "llm": {"model": "ollama/llama3", "temperature": 0},
            "verbose": False,
            "headless": True,
        }
        graph = SmartScraperGraph(prompt=prompt, source=url, config=graph_config)
        return graph.run()

    def _validate_public_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ScrapeGraphPolicyError("Only HTTP(S) public URLs are allowed.")
        if parsed.hostname is None:
            raise ScrapeGraphPolicyError("URL must include a hostname.")
        if not self._settings.scrapegraph_use_only_public_urls:
            return
        if _is_private_hostname(parsed.hostname):
            raise ScrapeGraphPolicyError("Private, loopback, and metadata hosts are not allowed.")


def _is_private_hostname(hostname: str) -> bool:
    lowered = hostname.lower().strip(".")
    if lowered in {"localhost", "metadata.google.internal"}:
        return True
    try:
        ip = ipaddress.ip_address(lowered)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(lowered, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return True
    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return True
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            return True
    return lowered in {"169.254.169.254", "100.100.100.200"}
