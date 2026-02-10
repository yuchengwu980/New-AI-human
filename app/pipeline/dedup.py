import hashlib
import time


class Deduplicator:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, float] = {}

    def hit(self, user_id: str, text: str) -> bool:
        now = time.time()
        self._cleanup(now)
        key = self._key(user_id, text)
        if key in self._cache and now - self._cache[key] < self.ttl_seconds:
            return True
        self._cache[key] = now
        return False

    @staticmethod
    def _key(user_id: str, text: str) -> str:
        return hashlib.sha256(f'{user_id}:{text}'.encode('utf-8')).hexdigest()

    def _cleanup(self, now: float) -> None:
        stale = [k for k, ts in self._cache.items() if now - ts >= self.ttl_seconds]
        for k in stale:
            self._cache.pop(k, None)
