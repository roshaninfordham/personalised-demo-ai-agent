"""Service resource metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceResource:
    service_name: str
    service_version: str
    environment: str

    def attributes(self) -> dict[str, str]:
        return {
            "service.name": self.service_name,
            "service.version": self.service_version,
            "deployment.environment": self.environment,
        }
