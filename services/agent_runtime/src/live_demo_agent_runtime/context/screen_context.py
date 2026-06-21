"""Screen context normalization helpers."""

from urllib.parse import urlparse

VOLATILE_QUERY_PREFIXES = ("utm_",)
VOLATILE_QUERY_KEYS = {"fbclid", "gclid", "timestamp", "t", "cache", "session", "token"}


def normalize_url_path(url: str) -> str:
    parsed = urlparse(url)
    path = (parsed.path or "/").lower()
    if len(path) > 1:
        path = path.rstrip("/")
    return path


def contains_forbidden_prompt_data(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in (
            "<html",
            "document.cookie",
            "localstorage",
            "sessionstorage",
            "data:image",
            "base64,",
            "api_key",
            "password",
            "secret",
        )
    )
