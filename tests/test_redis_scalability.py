from redis.exceptions import RedisError

import app.utils.database as database_module
from app.builder.response_builder import ResponseBuilder
from app.orchestrator.orchestrator import Orchestrator
from app.services.query_service import QueryService
from app.utils.cache import (
    InMemoryTTLCache,
    RedisTTLCache,
    create_cache_backend,
    get_cache_backend_name,
    get_cache_prefix,
    get_redis_client,
    get_redis_url,
)


class FakeRedisClient:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ping_called = False

    def ping(self) -> bool:
        self.ping_called = True
        return True

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.store[key] = value

    def scan_iter(self, match: str):
        prefix = match[:-1]
        for key in list(self.store.keys()):
            if key.startswith(prefix):
                yield key

    def delete(self, *keys: str) -> None:
        for key in keys:
            self.store.pop(key, None)


class CountingDataService:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_data(self, query) -> dict[str, object]:
        self.calls += 1
        return {"intent": query.intent.value, "entity": query.entity, "total": 2}


class CountingLLMService:
    def __init__(self) -> None:
        self.calls = 0

    def generate_text(self, user_input: str, data: dict[str, object]) -> str:
        self.calls += 1
        return f"Synthetic answer for {data['intent']}"

    def generate_fallback_text(
        self, user_input: str, data: dict[str, object] | None = None
    ) -> str:
        return "fallback"


def test_redis_ttl_cache_set_get_and_clear() -> None:
    redis_client = FakeRedisClient()
    cache = RedisTTLCache[str](
        namespace="response",
        ttl_seconds=60,
        redis_client=redis_client,
        prefix="laborit",
    )

    cache.set("key-1", "value-1")

    assert cache.get("key-1") == "value-1"

    cache.clear()
    assert cache.get("key-1") is None


def test_create_cache_backend_returns_redis_when_available(monkeypatch) -> None:
    fake_client = FakeRedisClient()

    monkeypatch.setenv("CACHE_BACKEND", "redis")
    monkeypatch.setenv("CACHE_PREFIX", "laborit")
    monkeypatch.setattr("app.utils.cache.get_redis_client", lambda: fake_client)

    cache = create_cache_backend(namespace="data", ttl_seconds=60)

    assert cache.backend_name == "redis"


def test_create_cache_backend_falls_back_when_redis_fails(monkeypatch) -> None:
    monkeypatch.setenv("CACHE_BACKEND", "redis")

    def fail_client():
        raise RedisError("redis unavailable")

    monkeypatch.setattr("app.utils.cache.get_redis_client", fail_client)

    cache = create_cache_backend(namespace="data", ttl_seconds=60)

    assert isinstance(cache, InMemoryTTLCache)
    assert cache.backend_name == "in-memory-fallback"


def test_cache_helpers_and_redis_client_creation(monkeypatch) -> None:
    fake_client = FakeRedisClient()

    monkeypatch.setenv("CACHE_BACKEND", "redis")
    monkeypatch.setenv("REDIS_URL", "redis://cache:6379/1")
    monkeypatch.setenv("CACHE_PREFIX", "copilot")
    get_redis_client.cache_clear()
    monkeypatch.setattr(
        "app.utils.cache.Redis.from_url", lambda *args, **kwargs: fake_client
    )

    assert get_cache_backend_name() == "redis"
    assert get_redis_url() == "redis://cache:6379/1"
    assert get_cache_prefix() == "copilot"
    assert get_redis_client() is fake_client
    assert fake_client.ping_called is True


def test_orchestrator_uses_redis_response_cache_and_metadata() -> None:
    redis_client = FakeRedisClient()
    response_cache = RedisTTLCache[str](
        namespace="response",
        ttl_seconds=120,
        redis_client=redis_client,
        prefix="laborit",
    )
    data_cache = RedisTTLCache[dict[str, object]](
        namespace="data",
        ttl_seconds=120,
        redis_client=redis_client,
        prefix="laborit",
    )
    data_service = CountingDataService()
    llm_service = CountingLLMService()
    orchestrator = Orchestrator(
        query_service=QueryService(),
        data_service=data_service,  # type: ignore[arg-type]
        llm_service=llm_service,  # type: ignore[arg-type]
        response_builder=ResponseBuilder(),
        data_cache=data_cache,
        response_cache=response_cache,
    )

    first = orchestrator.run("How many customers do we have?")
    second = orchestrator.run("How many customers do we have?")

    assert data_service.calls == 1
    assert llm_service.calls == 1
    assert first["metadata"]["cache"]["backend"] == "redis"
    assert first["metadata"]["cache"]["response_backend"] == "redis"
    assert first["metadata"]["cache"]["data_backend"] == "redis"
    assert second["metadata"]["cache"]["response_cache"] == "hit"


def test_orchestrator_uses_redis_data_cache_across_different_questions() -> None:
    redis_client = FakeRedisClient()
    response_cache = RedisTTLCache[str](
        namespace="response",
        ttl_seconds=120,
        redis_client=redis_client,
        prefix="laborit",
    )
    data_cache = RedisTTLCache[dict[str, object]](
        namespace="data",
        ttl_seconds=120,
        redis_client=redis_client,
        prefix="laborit",
    )
    data_service = CountingDataService()
    llm_service = CountingLLMService()
    orchestrator = Orchestrator(
        query_service=QueryService(),
        data_service=data_service,  # type: ignore[arg-type]
        llm_service=llm_service,  # type: ignore[arg-type]
        response_builder=ResponseBuilder(),
        data_cache=data_cache,
        response_cache=response_cache,
    )

    first = orchestrator.run("How many customers do we have?")
    second = orchestrator.run("How many customers are there in total?")

    assert data_service.calls == 1
    assert llm_service.calls == 2
    assert first["metadata"]["cache"]["data_cache"] == "miss"
    assert second["metadata"]["cache"]["data_cache"] == "hit"


def test_database_health_success_path(monkeypatch) -> None:
    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, statement) -> None:
            return None

    class FakeEngine:
        def connect(self):
            return FakeConnection()

    monkeypatch.setattr("app.utils.database.get_engine", lambda: FakeEngine())

    ok, detail = database_module.check_database_connection()

    assert ok is True
    assert detail == "Database connection ok"
