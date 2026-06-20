"""Development auth, URL validation, and input safety helpers."""

from __future__ import annotations

import ipaddress
import json
import re
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

from live_demo_api.config import ApiSettings
from live_demo_api.errors import UnauthorizedError, ValidationAppError

ALLOWED_ROLES = {"owner", "admin", "demo_builder", "viewer", "agent_runtime"}
SECRET_KEYS = {
    "password",
    "api_key",
    "secret",
    "token",
    "private_key",
    "client_secret",
    "refresh_token",
    "access_token",
}
BLOCKED_ALLOWED_ACTION_WORDS = {
    "delete",
    "remove",
    "payment",
    "billing",
    "send",
    "publish",
    "invite",
}
STEP_KEY_RE = re.compile(r"^[a-z0-9_\-]+$")


@dataclass(frozen=True)
class Principal:
    organization_id: UUID
    user_id: UUID | None
    role: str
    actor_type: str


@dataclass(frozen=True)
class RequestContext:
    request_id: str
    trace_id: str


def normalize_product_url(raw_url: str, settings: ApiSettings) -> str:
    if not raw_url or len(raw_url) > settings.max_product_url_length:
        raise ValidationAppError("Product URL is invalid.", code="invalid_product_url")
    parsed = urlsplit(raw_url.strip())
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValidationAppError("Product URL must use http or https.", code="invalid_product_url")
    if not parsed.hostname:
        raise ValidationAppError("Product URL must include a hostname.", code="invalid_product_url")
    hostname = parsed.hostname.lower()
    if _is_blocked_hostname(hostname) and not (
        settings.app_env == "local" and settings.allow_local_product_urls
    ):
        raise ValidationAppError(
            "Local/private product URLs are not allowed.", code="blocked_product_url"
        )
    netloc = hostname
    if parsed.port is not None:
        netloc = f"{hostname}:{parsed.port}"
    query = urlencode(parse_qsl(parsed.query, keep_blank_values=True), doseq=True)
    return urlunsplit((scheme, netloc, parsed.path or "", query, ""))


def _is_blocked_hostname(hostname: str) -> bool:
    if hostname == "localhost":
        return True
    try:
        ip_address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    blocked_networks = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
    ]
    return any(ip_address in network for network in blocked_networks)


def parse_principal_headers(
    *,
    organization_id: str | None,
    user_id: str | None,
    role: str | None,
    settings: ApiSettings,
) -> Principal:
    if organization_id is None:
        if not (settings.app_env == "local" and settings.dev_allow_implicit_local_org):
            raise UnauthorizedError("Missing organization header.", code="missing_organization")
        organization_id = settings.dev_local_organization_id
        user_id = user_id or settings.dev_local_user_id
        role = role or settings.dev_local_user_role
    parsed_role = role or settings.dev_local_user_role
    if parsed_role not in ALLOWED_ROLES:
        raise UnauthorizedError("Invalid local user role.", code="invalid_role")
    try:
        parsed_organization_id = UUID(organization_id)
        parsed_user_id = UUID(user_id) if user_id else None
    except ValueError as exc:
        raise UnauthorizedError("Invalid local auth headers.", code="invalid_auth_headers") from exc
    return Principal(
        organization_id=parsed_organization_id,
        user_id=parsed_user_id,
        role=parsed_role,
        actor_type="user" if parsed_user_id is not None else "system",
    )


def validate_no_secret_keys(
    value: object,
    *,
    max_depth: int,
    max_keys: int,
    path: str = "$",
) -> None:
    key_count = 0

    def visit(node: object, depth: int, current_path: str) -> None:
        nonlocal key_count
        if depth > max_depth:
            raise ValidationAppError(
                "Guidance content is too large or deep.",
                code="guidance_too_large_or_deep",
                details={"path": current_path},
            )
        if isinstance(node, dict):
            key_count += len(node)
            if key_count > max_keys:
                raise ValidationAppError(
                    "Guidance content is too large or deep.",
                    code="guidance_too_large_or_deep",
                    details={"path": current_path},
                )
            for key, child in node.items():
                lowered = str(key).lower()
                if lowered in SECRET_KEYS or any(secret in lowered for secret in SECRET_KEYS):
                    raise ValidationAppError(
                        "Guidance content must not contain secrets.",
                        code="guidance_contains_secret",
                        details={"path": f"{current_path}.{key}"},
                    )
                visit(child, depth + 1, f"{current_path}.{key}")
        elif isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, depth + 1, f"{current_path}[{index}]")

    visit(value, 0, path)


def serialized_json_size(value: object) -> int:
    return len(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


class RateLimiter(Protocol):
    async def check(self, key: str, limit: int, window_seconds: int) -> None: ...


class NoopRateLimiter:
    async def check(self, key: str, limit: int, window_seconds: int) -> None:
        _ = (key, limit, window_seconds)
