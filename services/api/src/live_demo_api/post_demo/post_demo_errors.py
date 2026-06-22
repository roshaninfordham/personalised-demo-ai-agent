"""Post-demo intelligence errors."""

from __future__ import annotations


class PostDemoError(Exception):
    """Base post-demo error."""


class EvidenceValidationError(PostDemoError):
    """Raised when generated output references missing evidence."""


class CrmConfigurationError(PostDemoError):
    """Raised when CRM export configuration is invalid."""


class CrmExportError(PostDemoError):
    """Raised when CRM export fails."""
