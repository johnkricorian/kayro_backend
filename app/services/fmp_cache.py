import time
from threading import Lock
from typing import Any

class FMPCache:
    def __init__(
        self,
        ttl_seconds: int = 3600
    ):
        self.ttl_seconds = ttl_seconds
        self._values: dict[str, tuple[float, Any]] = {}
        self._lock = Lock()

    def get(
        self,
        key: str
    ) -> Any | None:
        with self._lock:
            cached = self._values.get(key)

            if cached is None:
                return None

            created_at, value = cached

            if time.time() - created_at >= self.ttl_seconds:
                del self._values[key]
                return None

            return value

    def set(
        self,
        key: str,
        value: Any
    ) -> None:
        with self._lock:
            self._values[key] = (
                time.time(),
                value
            )

    def clear(self) -> None:
        with self._lock:
            self._values.clear()


fmp_reference_cache = FMPCache(
    ttl_seconds=86_400
)
