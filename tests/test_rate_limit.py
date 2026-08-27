from app.security.rate_limit import InMemoryRateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_rate_limiter_resets_after_window() -> None:
    clock = FakeClock()
    limiter = InMemoryRateLimiter(limit=1, window_seconds=10, clock=clock)

    assert limiter.check("reader") is None
    assert limiter.check("reader") == 10

    clock.now = 11.0
    assert limiter.check("reader") is None


def test_rate_limiter_separates_clients() -> None:
    limiter = InMemoryRateLimiter(limit=1, window_seconds=10, clock=lambda: 0.0)

    assert limiter.check("reader") is None
    assert limiter.check("admin") is None
