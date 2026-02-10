import time
from collections import deque


class RateLimiter:
    def __init__(self, user_window_seconds: int = 10, global_window_seconds: int = 1, global_max: int = 3) -> None:
        self.user_window_seconds = user_window_seconds
        self.global_window_seconds = global_window_seconds
        self.global_max = global_max
        self._last_user_ts: dict[str, float] = {}
        self._global_hits: deque[float] = deque()

    def hit(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup_global(now)

        user_last = self._last_user_ts.get(user_id)
        if user_last and now - user_last < self.user_window_seconds:
            return True

        if len(self._global_hits) >= self.global_max:
            return True

        self._last_user_ts[user_id] = now
        self._global_hits.append(now)
        return False

    def _cleanup_global(self, now: float) -> None:
        while self._global_hits and now - self._global_hits[0] >= self.global_window_seconds:
            self._global_hits.popleft()
