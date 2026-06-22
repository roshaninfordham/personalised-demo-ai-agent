"""Errors raised by secret providers."""


class SecretProviderError(RuntimeError):
    """Base secret provider failure."""


class SecretNotFoundError(SecretProviderError):
    """Raised when a required secret is missing."""


class UnsafeSecretConfigurationError(SecretProviderError):
    """Raised when production is configured to use an unsafe secret source."""
