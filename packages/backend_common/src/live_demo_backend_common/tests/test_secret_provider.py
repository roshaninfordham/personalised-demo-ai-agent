import pytest

from live_demo_backend_common.secrets import EnvSecretProvider
from live_demo_backend_common.secrets.secret_errors import SecretNotFoundError


@pytest.mark.asyncio
async def test_secret_value_repr_redacts_value() -> None:
    provider = EnvSecretProvider({"JWT_SECRET": "super-secret"})
    value = await provider.get_secret("JWT_SECRET")

    assert value.reveal() == "super-secret"
    assert "super-secret" not in repr(value)
    assert str(value) == "***REDACTED***"


@pytest.mark.asyncio
async def test_missing_required_secret_raises_safe_error() -> None:
    provider = EnvSecretProvider({})

    with pytest.raises(SecretNotFoundError):
        await provider.get_secret("JWT_SECRET")


@pytest.mark.asyncio
async def test_optional_secret_returns_none() -> None:
    provider = EnvSecretProvider({})

    assert await provider.get_optional_secret("JWT_SECRET") is None
