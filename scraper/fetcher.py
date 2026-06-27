from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable

import httpx


class FetchError(RuntimeError):
    """Raised when a URL cannot be retrieved after retries."""

    def __init__(self, url: str, message: str, status: int | None = None) -> None:
        super().__init__(f"{url}: {message}")
        self.url = url
        self.status = status


@runtime_checkable
class Fetcher(Protocol):
    async def get(self, url: str, *, headers: dict[str, str] | None = None) -> str: ...


class HttpxFetcher:
    """HTTP fetcher with bounded retries on network errors and 5xx responses."""

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        max_retries: int = 2,
        backoff: float = 0.5,
        client: httpx.AsyncClient | None = None,
        sleep=asyncio.sleep,
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff = backoff
        self._client = client
        self._sleep = sleep

    async def get(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        client = self._client or httpx.AsyncClient(
            timeout=self._timeout, follow_redirects=True
        )
        try:
            last_error: Exception | None = None
            for attempt in range(self._max_retries + 1):
                try:
                    response = await client.get(url, headers=headers)
                    if response.status_code >= 500:
                        raise FetchError(
                            url, f"server error {response.status_code}", response.status_code
                        )
                    if response.status_code >= 400:
                        raise FetchError(
                            url, f"client error {response.status_code}", response.status_code
                        )
                    return response.text
                except (httpx.TransportError, FetchError) as exc:
                    # 4xx is not retryable; surface it immediately.
                    if isinstance(exc, FetchError) and exc.status and exc.status < 500:
                        raise
                    last_error = exc
                    if attempt < self._max_retries:
                        await self._sleep(self._backoff * (2**attempt))
            raise FetchError(url, f"giving up after retries: {last_error}")
        finally:
            if self._client is None:
                await client.aclose()
