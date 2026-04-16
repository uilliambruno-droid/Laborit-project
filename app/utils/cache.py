import json
import os
from dataclasses import dataclass
from functools import lru_cache
from threading import Lock
from time import monotonic
from typing import Generic, Protocol, TypeVar, cast

from redis import Redis
from redis.exceptions import RedisError

ValueType = TypeVar("ValueType")


class CacheBackend(Protocol[ValueType]):
    backend_name: str

    def get(self, key: str) -> ValueType | None: ...

    def set(self, key: str, value: ValueType) -> None: ...

    def clear(self) -> None: ...


@dataclass
class CacheEntry(Generic[ValueType]):
    value: ValueType
    expires_at: float


class InMemoryTTLCache(Generic[ValueType]):
    def __init__(
        self,
        ttl_seconds: int = 60,
        backend_name: str = "in-memory",
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.backend_name = backend_name
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


class RedisTTLCache(Generic[ValueType]):
    def __init__(
        self,
        *,
        namespace: str,
        ttl_seconds: int = 60,
        redis_client: Redis,
        prefix: str = "laborit",
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.backend_name = "redis"
        self.namespace = namespace
        self.redis_client = redis_client
        self.prefix = prefix

    def _build_key(self, key: str) -> str:
        return f"{self.prefix}:{self.namespace}:{key}"

    def get(self, key: str) -> ValueType | None:
        raw_value = self.redis_client.get(self._build_key(key))
        if raw_value is None:
            return None
        return cast(ValueType, json.loads(raw_value))

    def set(self, key: str, value: ValueType) -> None:
        self.redis_client.setex(
            self._build_key(key),
            self.ttl_seconds,
            json.dumps(value),
        )

    def clear(self) -> None:
        keys = list(
            self.redis_client.scan_iter(match=f"{self.prefix}:{self.namespace}:*")
        )
        if keys:
            self.redis_client.delete(*keys)


def get_cache_backend_name() -> str:
    return os.getenv("CACHE_BACKEND", "in-memory").strip().lower()


def get_redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_cache_prefix() -> str:
    return os.getenv("CACHE_PREFIX", "laborit")


@lru_cache
def get_redis_client() -> Redis:
    client = Redis.from_url(get_redis_url(), decode_responses=True)
    client.ping()
    return client


def create_cache_backend(
    *,
    namespace: str,
    ttl_seconds: int,
) -> CacheBackend[object]:
    backend = get_cache_backend_name()

    if backend == "redis":
        try:
            return RedisTTLCache(
                namespace=namespace,
                ttl_seconds=ttl_seconds,
                redis_client=get_redis_client(),
                prefix=get_cache_prefix(),
            )
        except (RedisError, ValueError, OSError):
            return InMemoryTTLCache(
                ttl_seconds=ttl_seconds,
                backend_name="in-memory-fallback",
            )

    return InMemoryTTLCache(ttl_seconds=ttl_seconds)
