import pytest

from ras.common.integration.connection import (
    DEFAULT_TIMEOUT,
    RETRY_COUNT,
    WRITE_TIMEOUT,
    AsyncExternalClient,
    ExternalClient,
)


def test_sync_external_client_applies_default_options():
    client = ExternalClient()
    assert client.timeout.connect == DEFAULT_TIMEOUT
    assert client.timeout.read == DEFAULT_TIMEOUT
    assert client.timeout.write == WRITE_TIMEOUT
    assert client.timeout.pool is None
    assert client._transport._pool._retries == RETRY_COUNT  # type: ignore[attr-defined]
    assert client._transport._pool._http2 is True  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_async_external_client_applies_default_options():
    async with AsyncExternalClient() as client:
        assert client.timeout.connect == DEFAULT_TIMEOUT
        assert client.timeout.read == DEFAULT_TIMEOUT
        assert client.timeout.write == WRITE_TIMEOUT
        assert client.timeout.pool is None
        assert client._transport._pool._retries == RETRY_COUNT  # type: ignore[attr-defined]
        assert client._transport._pool._http2 is True  # type: ignore[attr-defined]
