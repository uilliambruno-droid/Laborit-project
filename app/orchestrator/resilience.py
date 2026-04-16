from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from time import perf_counter
from typing import TypeVar

from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

ResultType = TypeVar("ResultType")


def run_step(
    *,
    step_name: str,
    steps: list[dict[str, object]],
    executor: Callable[[], ResultType],
) -> ResultType:
    started_at = perf_counter()
    result = executor()
    steps.append(
        {
            "step": step_name,
            "status": "ok",
            "duration_ms": round((perf_counter() - started_at) * 1000, 2),
        }
    )
    return result


def run_with_resilience(
    *,
    breaker: CircuitBreaker,
    timeout_seconds: float,
    retry_attempts: int,
    steps: list[dict[str, object]],
    step_name: str,
    executor: Callable[[], ResultType],
) -> ResultType:
    last_error: Exception | None = None

    for attempt in range(1, retry_attempts + 1):
        started_at = perf_counter()
        try:
            breaker.before_call()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(executor)
                result = future.result(timeout=timeout_seconds)
            breaker.record_success()
            steps.append(
                {
                    "step": step_name,
                    "status": "ok",
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    "attempt": attempt,
                }
            )
            return result
        except CircuitBreakerOpenError as error:
            steps.append(
                {
                    "step": step_name,
                    "status": "circuit-open",
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    "attempt": attempt,
                }
            )
            raise RuntimeError(str(error)) from error
        except FutureTimeoutError as error:
            breaker.record_failure()
            last_error = error
            steps.append(
                {
                    "step": step_name,
                    "status": "timeout",
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    "attempt": attempt,
                }
            )
        except (
            Exception
        ) as error:  # pragma: no cover - exercised through service failure tests
            breaker.record_failure()
            last_error = error
            steps.append(
                {
                    "step": step_name,
                    "status": "error",
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    "attempt": attempt,
                    "error_type": error.__class__.__name__,
                }
            )

    raise RuntimeError(f"Step '{step_name}' failed after retries") from last_error
