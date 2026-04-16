"""Utility package."""

from app.utils.cache import (
    CacheBackend,
    InMemoryTTLCache,
    RedisTTLCache,
    create_cache_backend,
    get_cache_backend_name,
    get_redis_client,
)
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from app.utils.database import check_database_connection, get_database_url, get_engine
from app.utils.metrics import metrics_registry
from app.utils.security import API_KEY_HEADER, get_expected_api_key, require_api_key

__all__ = [
    "CacheBackend",
    "InMemoryTTLCache",
    "RedisTTLCache",
    "create_cache_backend",
    "get_cache_backend_name",
    "get_redis_client",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "check_database_connection",
    "get_database_url",
    "get_engine",
    "metrics_registry",
    "API_KEY_HEADER",
    "get_expected_api_key",
    "require_api_key",
]
