import httpx

DEFAULT_TIMEOUT = 10  # in seconds
WRITE_TIMEOUT = 60
RETRY_COUNT = 3

_timeout = httpx.Timeout(DEFAULT_TIMEOUT, write=WRITE_TIMEOUT, pool=None)
_retry_sync = httpx.HTTPTransport(http2=True, retries=RETRY_COUNT)
_retry_async = httpx.AsyncHTTPTransport(http2=True, retries=RETRY_COUNT)


class ExternalClient(httpx.Client):
    def __init__(self, *args, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = _timeout
        if "transport" not in kwargs:
            kwargs["transport"] = _retry_sync
        super().__init__(*args, **kwargs)


class AsyncExternalClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = _timeout
        if "transport" not in kwargs:
            kwargs["transport"] = _retry_async
        super().__init__(*args, **kwargs)
