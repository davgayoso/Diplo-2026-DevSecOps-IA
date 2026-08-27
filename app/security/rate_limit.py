from collections import defaultdict, deque
from collections.abc import Callable
from math import ceil
from threading import Lock
from time import monotonic


class InMemoryRateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: int,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def check(self, client_id: str) -> int | None:
        now = self.clock()
        cutoff = now - self.window_seconds

        with self.lock:
            timestamps = self.requests[client_id]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= self.limit:
                return max(1, ceil(self.window_seconds - (now - timestamps[0])))

            timestamps.append(now)
            return None
