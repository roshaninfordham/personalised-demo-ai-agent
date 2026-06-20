"""Deterministic artifact object-key builders."""

import re
from uuid import UUID

ALLOWED_EXTENSIONS = {"webp", "png", "jpg", "jpeg", "wav", "mp3", "zip", "json", "txt"}
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def _uuid_segment(value: str) -> str:
    return str(UUID(value))


def _extension(value: str) -> str:
    cleaned = value.lower().lstrip(".")
    if cleaned not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported artifact extension: {value}")
    return cleaned


def _safe_name(value: str) -> str:
    if "/" in value or "\\" in value or ".." in value:
        raise ValueError("Object name must not contain path separators or traversal")
    cleaned = SAFE_NAME_RE.sub("-", value.strip()).strip(".-/")
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("Object name must contain at least one safe character")
    return cleaned


def _assert_safe_key(object_key: str) -> str:
    if object_key.startswith("/") or ".." in object_key:
        raise ValueError("Object key must not be absolute or contain traversal")
    return object_key


def screenshot_key(
    organization_id: str,
    session_id: str,
    screen_id: str,
    extension: str = "webp",
) -> str:
    return _assert_safe_key(
        "org/"
        f"{_uuid_segment(organization_id)}/sessions/{_uuid_segment(session_id)}"
        f"/screenshots/{_uuid_segment(screen_id)}.{_extension(extension)}"
    )


def browser_trace_key(
    organization_id: str,
    session_id: str,
    trace_id: str,
) -> str:
    return _assert_safe_key(
        "org/"
        f"{_uuid_segment(organization_id)}/sessions/{_uuid_segment(session_id)}"
        f"/browser-traces/{_safe_name(trace_id)}.zip"
    )


def recording_key(
    organization_id: str,
    session_id: str,
    recording_id: str,
    extension: str = "wav",
) -> str:
    return _assert_safe_key(
        "org/"
        f"{_uuid_segment(organization_id)}/sessions/{_uuid_segment(session_id)}"
        f"/recordings/{_uuid_segment(recording_id)}.{_extension(extension)}"
    )


def generated_report_key(
    organization_id: str,
    session_id: str,
    report_name: str,
    extension: str = "json",
) -> str:
    return _assert_safe_key(
        "org/"
        f"{_uuid_segment(organization_id)}/sessions/{_uuid_segment(session_id)}"
        f"/reports/{_safe_name(report_name)}.{_extension(extension)}"
    )
