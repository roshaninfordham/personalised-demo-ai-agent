"""Browser runtime client abstraction for orchestration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import quote, urlsplit
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


class BrowserRuntimeUnavailable(RuntimeError):
    """Raised when the real browser runtime cannot provide a live browser result."""


class BrowserRuntimeClient:
    """Browser-runtime facade.

    Real demo mode must never synthesize product screens. A deterministic fallback exists only
    behind BROWSER_RUNTIME_ENABLE_MOCK_FALLBACK for explicitly labelled fixture/demo tests.
    """

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
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            if not settings.browser_runtime_enable_mock_fallback:
                raise BrowserRuntimeUnavailable("browser_runtime_session_create_failed") from exc
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
        except httpx.HTTPError as exc:
            if not settings.browser_runtime_enable_mock_fallback:
                raise BrowserRuntimeUnavailable("browser_runtime_navigation_failed") from exc
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
        except (httpx.HTTPError, ValueError) as exc:
            if not settings.browser_runtime_enable_mock_fallback:
                raise BrowserRuntimeUnavailable("browser_runtime_screen_read_failed") from exc
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
            "summary": f"Fixture demo screen for {title}.",
            "screen_hash": digest,
            "confidence": 0.72,
            "image_url": "",
            "width": 1440,
            "height": 900,
            "diagnostics": {
                "mock_fallback": True,
                "navigation_status": "fixture_mode",
                "warnings": ["This is a fixture fallback, not a real browser screenshot."],
            },
            "updated_at": datetime.now(UTC).isoformat(),
        }
        safe_actions = _fallback_safe_actions()
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
    elif isinstance(summary, str):
        summary_text = summary
    title = str(screen.get("title") or "")
    url = str(screen.get("url") or "")
    image_url = str(screen.get("image_url") or screen.get("screenshot_url") or "")
    screenshot_uri = str(screen.get("screenshot_uri") or "")
    if not image_url and screenshot_uri:
        image_url = _artifact_content_url(screenshot_uri)
    elements = screen.get("elements")
    width = _int_value(screen.get("width"), 1440)
    height = _int_value(screen.get("height"), 900)
    diagnostics = screen.get("diagnostics")
    return {
        "screen_id": str(screen.get("screen_id") or ""),
        "browser_session_id": str(screen.get("browser_session_id") or ""),
        "url": url,
        "url_path": urlsplit(url).path or "/",
        "title": title,
        "summary": summary_text,
        "screen_hash": str(screen.get("screen_hash") or ""),
        "image_url": image_url,
        "screenshot_uri": screenshot_uri,
        "width": width,
        "height": height,
        "elements": elements if isinstance(elements, list) else [],
        "confidence": _float_value(screen.get("confidence")),
        "diagnostics": diagnostics if isinstance(diagnostics, dict) else {},
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


def _int_value(value: object, fallback: int) -> int:
    if isinstance(value, int | float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return fallback
    return fallback


def _artifact_content_url(object_key: str) -> str:
    return f"/api/v1/artifacts/browser-screenshot?object_key={quote(object_key, safe='')}"


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
                    "bbox": element.get("bbox") if isinstance(element.get("bbox"), dict) else None,
                }
            )
    return tuple(actions)


def _fallback_safe_actions() -> tuple[dict[str, object], ...]:
    return (
        {
            "action_id": "act_read_current_screen",
            "action_type": "read_current_screen",
            "label": "Read current screen",
            "risk_level": "low",
            "score": 1.0,
            "requires_confirmation": False,
        },
    )
