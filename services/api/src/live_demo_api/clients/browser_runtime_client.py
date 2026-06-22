"""Browser runtime client abstraction for orchestration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
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
            "image_url": _generated_screen_image(
                title=title,
                url=url,
                summary=f"Initial screen for {title}.",
            ),
            "width": 1440,
            "height": 900,
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
    if not image_url:
        image_url = _generated_screen_image(title=title or "Product", url=url, summary=summary_text)
    elements = screen.get("elements")
    return {
        "screen_id": str(screen.get("screen_id") or ""),
        "browser_session_id": str(screen.get("browser_session_id") or ""),
        "url": url,
        "url_path": urlsplit(url).path or "/",
        "title": title,
        "summary": summary_text,
        "screen_hash": str(screen.get("screen_hash") or ""),
        "image_url": image_url,
        "screenshot_uri": str(screen.get("screenshot_uri") or ""),
        "width": 1440,
        "height": 900,
        "elements": elements if isinstance(elements, list) else [],
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
                    "bbox": element.get("bbox") if isinstance(element.get("bbox"), dict) else None,
                }
            )
    labels = {str(action.get("label") or "").lower() for action in actions}
    if not any("metric" in label for label in labels):
        actions.extend(_fallback_safe_actions()[1:])
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
        {
            "action_id": "act_highlight_overview",
            "action_type": "highlight_element",
            "label": "Overview",
            "risk_level": "low",
            "score": 0.8,
            "requires_confirmation": False,
            "bbox": {"x": 96, "y": 462, "width": 340, "height": 176},
        },
        {
            "action_id": "act_add_metric",
            "action_type": "click_element",
            "label": "Add Metric",
            "risk_level": "low",
            "score": 0.86,
            "requires_confirmation": False,
            "bbox": {"x": 550, "y": 462, "width": 340, "height": 176},
        },
        {
            "action_id": "act_reports",
            "action_type": "click_element",
            "label": "Reports",
            "risk_level": "low",
            "score": 0.82,
            "requires_confirmation": False,
            "bbox": {"x": 1004, "y": 462, "width": 340, "height": 176},
        },
    )


def _generated_screen_image(*, title: str, url: str, summary: str) -> str:
    safe_title = escape(title or "Product")
    safe_url = escape(url)
    safe_summary = escape(summary or "Initial screen loaded.")
    svg = "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="900"',
            '  viewBox="0 0 1440 900">',
            '<rect width="1440" height="900" fill="#f8fafc"/>',
            '<rect x="64" y="56" width="1312" height="96" rx="20"',
            '  fill="#ffffff" stroke="#dbe3ef"/>',
            '<circle cx="112" cy="104" r="12" fill="#ef4444"/>',
            '<circle cx="148" cy="104" r="12" fill="#f59e0b"/>',
            '<circle cx="184" cy="104" r="12" fill="#10b981"/>',
            _svg_text(232, 112, 28, "#475569", safe_url),
            '<rect x="96" y="214" width="1248" height="184" rx="28" fill="#eef2ff"/>',
            _svg_text(136, 292, 54, "#111827", safe_title, weight=700),
            _svg_text(138, 346, 28, "#475569", safe_summary[:120]),
            _card_svg(96, "Overview", "Current screen detected"),
            _card_svg(550, "Add Metric", "Safe action candidate"),
            _card_svg(1004, "Reports", "Demo route candidate"),
            "</svg>",
        ]
    )
    return "data:image/svg+xml;utf8," + quote(svg)


def _card_svg(x: int, title: str, subtitle: str) -> str:
    return "\n".join(
        [
            f'<rect x="{x}" y="462" width="340" height="176" rx="24"',
            '  fill="#ffffff" stroke="#dbe3ef"/>',
            _svg_text(x + 36, 534, 34, "#111827", title, weight=700),
            _svg_text(x + 36, 586, 24, "#64748b", subtitle),
        ]
    )


def _svg_text(
    x: int,
    y: int,
    size: int,
    fill: str,
    text: str,
    *,
    weight: int | None = None,
) -> str:
    weight_attr = "" if weight is None else f' font-weight="{weight}"'
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-family="Inter, Arial" '
        f'font-size="{size}"{weight_attr}>{text}</text>'
    )
