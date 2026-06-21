from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class DomainMatcher:
    exact: frozenset[str]
    wildcard_suffixes: frozenset[str]

    @classmethod
    def compile(cls, domains: list[str] | tuple[str, ...]) -> DomainMatcher:
        exact: set[str] = set()
        wildcard: set[str] = set()
        for domain in domains:
            normalized = normalize_domain(domain)
            if normalized.startswith("*."):
                wildcard.add(normalized[2:])
            elif normalized:
                exact.add(normalized)
        return cls(frozenset(exact), frozenset(wildcard))

    def allows_host(self, host: str) -> bool:
        normalized = normalize_domain(host)
        if normalized in self.exact:
            return True
        return any(normalized.endswith(f".{suffix}") for suffix in self.wildcard_suffixes)


def normalize_domain(domain: str) -> str:
    return domain.strip().lower().rstrip(".")


def domain_allowed(url: str, allowed_domains: tuple[str, ...] | list[str]) -> bool:
    if not allowed_domains:
        return False
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return False
    if parsed.username or parsed.password:
        return False
    host = parsed.hostname.lower().rstrip(".")
    if _is_private_or_local(host):
        return False
    return DomainMatcher.compile(tuple(allowed_domains)).allows_host(host)


def _is_private_or_local(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified
