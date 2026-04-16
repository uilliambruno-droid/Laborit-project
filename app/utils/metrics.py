from collections import defaultdict
from threading import Lock
from time import perf_counter


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._started_at = perf_counter()
        self._http_requests_total = 0
        self._copilot_requests_total = 0
        self._fallback_total = 0
        self._response_cache_hits_total = 0
        self._response_cache_misses_total = 0
        self._data_cache_hits_total = 0
        self._data_cache_misses_total = 0
        self._duration_ms_sum = 0.0
        self._duration_ms_max = 0.0
        self._status_counts: dict[str, int] = defaultdict(int)
        self._path_counts: dict[str, int] = defaultdict(int)

    def record_http(self, path: str, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._http_requests_total += 1
            self._status_counts[str(status_code)] += 1
            self._path_counts[path] += 1
            self._duration_ms_sum += duration_ms
            self._duration_ms_max = max(self._duration_ms_max, duration_ms)

    def record_copilot_metadata(self, metadata: dict[str, object]) -> None:
        with self._lock:
            self._copilot_requests_total += 1
            if bool(metadata.get("fallback_used")):
                self._fallback_total += 1

            cache = metadata.get("cache", {})
            if isinstance(cache, dict):
                response_cache = str(cache.get("response_cache", ""))
                data_cache = str(cache.get("data_cache", ""))

                if response_cache == "hit":
                    self._response_cache_hits_total += 1
                elif response_cache == "miss":
                    self._response_cache_misses_total += 1

                if data_cache == "hit":
                    self._data_cache_hits_total += 1
                elif data_cache == "miss":
                    self._data_cache_misses_total += 1

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            elapsed_ms = (perf_counter() - self._started_at) * 1000
            avg_duration_ms = (
                round(self._duration_ms_sum / self._http_requests_total, 2)
                if self._http_requests_total
                else 0.0
            )

            return {
                "uptime_ms": round(elapsed_ms, 2),
                "http": {
                    "requests_total": self._http_requests_total,
                    "avg_duration_ms": avg_duration_ms,
                    "max_duration_ms": round(self._duration_ms_max, 2),
                    "status_counts": dict(self._status_counts),
                    "path_counts": dict(self._path_counts),
                },
                "copilot": {
                    "requests_total": self._copilot_requests_total,
                    "fallback_total": self._fallback_total,
                    "response_cache": {
                        "hit": self._response_cache_hits_total,
                        "miss": self._response_cache_misses_total,
                    },
                    "data_cache": {
                        "hit": self._data_cache_hits_total,
                        "miss": self._data_cache_misses_total,
                    },
                },
            }


metrics_registry = MetricsRegistry()
