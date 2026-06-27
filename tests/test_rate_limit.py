from scraper.rate_limit import RateLimiter


def _fake_clock_and_sleep():
    now = {"t": 0.0}
    slept: list[float] = []

    def clock() -> float:
        return now["t"]

    async def sleep(seconds: float) -> None:
        slept.append(seconds)
        now["t"] += seconds

    return clock, sleep, slept


async def test_spaces_requests_to_same_host():
    clock, sleep, slept = _fake_clock_and_sleep()
    limiter = RateLimiter(2.0, clock=clock, sleep=sleep)

    await limiter.acquire("https://a.example.com/1")
    await limiter.acquire("https://a.example.com/2")

    assert slept == [2.0]


async def test_independent_per_host():
    clock, sleep, slept = _fake_clock_and_sleep()
    limiter = RateLimiter(2.0, clock=clock, sleep=sleep)

    await limiter.acquire("https://a.example.com/1")
    await limiter.acquire("https://b.example.com/1")

    assert slept == []


async def test_zero_interval_never_waits():
    clock, sleep, slept = _fake_clock_and_sleep()
    limiter = RateLimiter(0, clock=clock, sleep=sleep)

    await limiter.acquire("https://a.example.com/1")
    await limiter.acquire("https://a.example.com/2")

    assert slept == []
