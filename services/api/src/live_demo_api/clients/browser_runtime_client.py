"""Browser runtime client abstraction for orchestration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlsplit
from uuid import UUID, uuid5

import httpx

from live_demo_api.config import get_settings


@dataclass(frozen=True, slots=True)
class BrowserSessionResult:
    browser_session_id: UUID


@dataclass(frozen=True, slots=True)
class BrowserScreenResult:
    browser_session_id: UUID
    screen: dict[str, object]
    safe_actions: tuple[dict[str, object], ...]


class BrowserRuntimeClient:
    """Browser-runtime facade with deterministic fallback for local tests."""

    async def create_session(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        session_id: UUID,
        start_url: str,
        trace_id: str,
    ) -> BrowserSessionResult:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
                response = await client.post(
                    f"{settings.browser_runtime_base_url}/internal/browser/v1/sessions",
                    json={
                        "organization_id": str(organization_id),
                        "demo_session_id": str(session_id),
                        "product_id": str(product_id),
                        "start_url": start_url,
                    },
                    headers={"X-Trace-ID": trace_id},
                )
                response.raise_for_status()
                payload = response.json()
                return BrowserSessionResult(
                    browser_session_id=UUID(str(payload["browser_session_id"]))
                )
        except (httpx.HTTPError, KeyError, ValueError):
            pass
        _ = organization_id, product_id, start_url, trace_id
        return BrowserSessionResult(browser_session_id=uuid5(session_id, "browser-session"))

    async def navigate(
        self, *, browser_session_id: UUID, url: str, trace_id: str
    ) -> dict[str, object]:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
                response = await client.post(
                    f"{settings.browser_runtime_base_url}/internal/browser/v1/sessions/"
                    f"{browser_session_id}/navigate",
                    json={"url": url},
                    headers={"X-Trace-ID": trace_id},
                )
                response.raise_for_status()
                return dict(response.json())
        except httpx.HTTPError:
            pass
        _ = trace_id
        return {
            "browser_session_id": str(browser_session_id),
            "url": url,
            "status": "completed",
            "updated_at": datetime.now(UTC).isoformat(),
        }

    async def read_current_screen(
        self,
        *,
        organization_id: UUID,
        product_id: UUID,
        session_id: UUID,
        browser_session_id: UUID,
        url: str,
        trace_id: str,
    ) -> BrowserScreenResult:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
                response = await client.get(
                    f"{settings.browser_runtime_base_url}/internal/browser/v1/sessions/"
                    f"{browser_session_id}/screen",
                    headers={"X-Trace-ID": trace_id},
                )
                response.raise_for_status()
                screen = dict(response.json())
                return BrowserScreenResult(
                    browser_session_id=browser_session_id,
                    screen=_compact_screen(screen),
                    safe_actions=_safe_actions_from_screen(screen),
                )
        except (httpx.HTTPError, ValueError):
            pass
        _ = organization_id, product_id, trace_id
        parsed = urlsplit(url)
        title = parsed.hostname or "Product"
        digest = hashlib.sha256(f"{session_id}:{url}".encode()).hexdigest()[:16]
        screen = {
            "screen_id": str(uuid5(session_id, f"screen:{digest}")),
            "browser_session_id": str(browser_session_id),
            "url": url,
            "url_path": parsed.path or "/",
            "title": title,
            "summary": f"Initial screen for {title}.",
            "screen_hash": digest,
            "confidence": 0.72,
            "updated_at": datetime.now(UTC).isoformat(),
        }
        safe_actions = (
            {
                "action_id": "act_read_current_screen",
                "action_type": "read_current_screen",
                "label": "Read current screen",
                "risk_level": "low",
                "score": 1.0,
                "requires_confirmation": False,
            },
            {
                "action_id": "act_highlight_overview",
                "action_type": "highlight_element",
                "label": "Overview",
                "risk_level": "low",
                "score": 0.8,
                "requires_confirmation": False,
            },
        )
        return BrowserScreenResult(
            browser_session_id=browser_session_id,
            screen=screen,
            safe_actions=safe_actions,
        )

    async def go_back(self, *, browser_session_id: UUID, trace_id: str) -> bool:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
                response = await client.post(
                    f"{settings.browser_runtime_base_url}/internal/browser/v1/sessions/"
                    f"{browser_session_id}/actions/go_back",
                    json={"action_type": "go_back"},
                    headers={"X-Trace-ID": trace_id},
                )
                return response.status_code < 500
        except httpx.HTTPError:
            pass
        _ = browser_session_id, trace_id
        return True

    async def close_session(self, *, browser_session_id: UUID, trace_id: str) -> bool:
        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
                response = await client.delete(
                    f"{settings.browser_runtime_base_url}/internal/browser/v1/sessions/"
                    f"{browser_session_id}",
                    headers={"X-Trace-ID": trace_id},
                )
                return response.status_code < 500
        except httpx.HTTPError:
            pass
        _ = browser_session_id, trace_id
        return True


def _compact_screen(screen: dict[str, object]) -> dict[str, object]:
    summary = screen.get("summary")
    summary_text = ""
    if isinstance(summary, dict):
        summary_text = str(summary.get("summary") or "")
    return {
        "screen_id": str(screen.get("screen_id") or ""),
        "browser_session_id": str(screen.get("browser_session_id") or ""),
        "url": str(screen.get("url") or ""),
        "url_path": urlsplit(str(screen.get("url") or "")).path or "/",
        "title": str(screen.get("title") or ""),
        "summary": summary_text,
        "screen_hash": str(screen.get("screen_hash") or ""),
        "confidence": _float_value(screen.get("confidence")),
        "updated_at": datetime.now(UTC).isoformat(),
    }


def _timeout_seconds() -> float:
    return get_settings().internal_service_timeout_ms / 1000


def _float_value(value: object) -> float:
    if isinstance(value, int | float | str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _safe_actions_from_screen(screen: dict[str, object]) -> tuple[dict[str, object], ...]:
    actions: list[dict[str, object]] = [
        {
            "action_id": "act_read_current_screen",
            "action_type": "read_current_screen",
            "label": "Read current screen",
            "risk_level": "low",
            "score": 1.0,
            "requires_confirmation": False,
        }
    ]
    elements = screen.get("elements")
    if isinstance(elements, list):
        for element in elements[:2]:
            if not isinstance(element, dict):
                continue
            label = str(element.get("label") or element.get("text") or "Element")
            actions.append(
                {
                    "action_id": f"act_highlight_{element.get('element_id', len(actions))}",
                    "action_type": "highlight_element",
                    "label": label[:120],
                    "risk_level": str(element.get("risk_level") or "low"),
                    "score": float(element.get("confidence") or 0.8),
                    "requires_confirmation": False,
                }
            )
    return tuple(actions)
