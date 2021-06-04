import asyncio
import logging

import httpx

DEFAULT_TIMEOUT = 10  # in seconds
WRITE_TIMEOUT = 60
RETRY_COUNT = 3

_timeout = httpx.Timeout(DEFAULT_TIMEOUT, write=WRITE_TIMEOUT, pool=None)
_retry_sync = httpx.HTTPTransport(http2=True, retries=RETRY_COUNT)
_retry_async = httpx.AsyncHTTPTransport(http2=True, retries=RETRY_COUNT)

logger = logging.getLogger(__name__)


class ExternalClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = _timeout
        if "transport" not in kwargs:
            kwargs["transport"] = _retry_sync
        kwargs["event_hooks"] = {"request": [self.log_request], "response": [self.log_response]}
        super().__init__(*args, **kwargs)

    def log_request(self, request):
        logger.debug(f"[External] Request hook: {request.method} {request.url} {request.content.decode()}")

    def log_response(self, response):
        request = response.request
        logger.debug(f"[External] Response hook: {request.method} {request.url} - {response.status_code}")


class AsyncExternalClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = _timeout
        if "transport" not in kwargs:
            kwargs["transport"] = _retry_async
        kwargs["event_hooks"] = {"request": [self.log_request], "response": [self.log_response]}
        super().__init__(*args, **kwargs)

    async def log_request(self, request):
        logger.debug(f"[AsyncExternal] Request hook: {request.method} {request.url} {request.content.decode()}")
        await asyncio.sleep(0)

    async def log_response(self, response):
        request = response.request
        logger.debug(f"[AsyncExternal] Response hook: {request.method} {request.url} - {response.status_code}")
        await asyncio.sleep(0)
