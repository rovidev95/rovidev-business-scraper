from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from urllib.parse import urlparse


class RateLimiter:
    """Per-host politeness delay.

    Ensures at least ``min_interval`` seconds elapse between requests to the same
    host. The clock and sleep functions are injectable so it can be tested
    without real waiting.
    """

    def __init__(
        self,
        min_interval: float = 1.0,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.min_interval = min_interval
        self._clock = clock
        self._sleep = sleep
        self._last_seen: dict[str, float] = {}

    async def acquire(self, url: str) -> None:
        if self.min_interval <= 0:
            return
        host = urlparse(url).netloc
        last = self._last_seen.get(host)
        now = self._clock()
        if last is not None:
            wait = self.min_interval - (now - last)
            if wait > 0:
                await self._sleep(wait)
        self._last_seen[host] = self._clock()
