from time import perf_counter


def build_request_metadata(
    *,
    trace_id: str,
    request_started_at: float,
    steps: list[dict[str, object]],
    fallback_used: bool,
    response_source: str,
    data_source: str,
    cache_status: dict[str, str],
    response_cache_backend: str,
    data_cache_backend: str,
    data_breaker_snapshot: dict[str, object],
    llm_breaker_snapshot: dict[str, object],
    intent: str | None,
) -> dict[str, object]:
    merged_backend = (
        response_cache_backend
        if response_cache_backend == data_cache_backend
        else "mixed"
    )
    return {
        "trace_id": trace_id,
        "intent": intent,
        "fallback_used": fallback_used,
        "response_source": response_source,
        "data_source": data_source,
        "cache": {
            **cache_status,
            "backend": merged_backend,
            "response_backend": response_cache_backend,
            "data_backend": data_cache_backend,
        },
        "circuit_breakers": {
            "data_service": data_breaker_snapshot,
            "llm_service": llm_breaker_snapshot,
        },
        "steps": steps,
        "total_duration_ms": round((perf_counter() - request_started_at) * 1000, 2),
    }
