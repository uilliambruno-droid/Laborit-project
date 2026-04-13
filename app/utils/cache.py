from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Generic, TypeVar

ValueType = TypeVar("ValueType")


@dataclass
class CacheEntry(Generic[ValueType]):
    value: ValueType
    expires_at: float


class InMemoryTTLCache(Generic[ValueType]):
    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl_seconds = ttl_seconds
        self.backend_name = "in-memory"
        self._store: dict[str, CacheEntry[ValueType]] = {}
        self._lock = Lock()

    def get(self, key: str) -> ValueType | None:
        now = monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None

            if entry.expires_at <= now:
                self._store.pop(key, None)
                return None

            return entry.value

    def set(self, key: str, value: ValueType) -> None:
        expires_at = monotonic() + self.ttl_seconds
        with self._lock:
            self._store[key] = CacheEntry(value=value, expires_at=expires_at)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
