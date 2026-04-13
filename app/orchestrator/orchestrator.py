from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from logging import getLogger
from time import perf_counter, sleep
from uuid import uuid4

from app.builder.response_builder import ResponseBuilder
from app.services.data_service import DataService
from app.services.llm_service import LLMService
from app.services.query_service import QueryService
from app.utils.cache import InMemoryTTLCache
from app.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

logger = getLogger(__name__)


class Orchestrator:
    SIMULATION_MARKERS = {
        "[[simulate:data-timeout]]": "data-timeout",
        "[[simulate:data-error]]": "data-error",
        "[[simulate:llm-timeout]]": "llm-timeout",
        "[[simulate:llm-error]]": "llm-error",
    }

    def __init__(
        self,
        query_service: QueryService | None = None,
        data_service: DataService | None = None,
        llm_service: LLMService | None = None,
        response_builder: ResponseBuilder | None = None,
        data_cache: InMemoryTTLCache[dict[str, object]] | None = None,
        response_cache: InMemoryTTLCache[str] | None = None,
        data_circuit_breaker: CircuitBreaker | None = None,
        llm_circuit_breaker: CircuitBreaker | None = None,
        data_timeout_seconds: float = 3.0,
        llm_timeout_seconds: float = 3.0,
        retry_attempts: int = 2,
    ) -> None:
        self.query_service = query_service or QueryService()
        self.data_service = data_service or DataService()
        self.llm_service = llm_service or LLMService()
        self.response_builder = response_builder or ResponseBuilder()
        self.data_cache = data_cache or InMemoryTTLCache(ttl_seconds=60)
        self.response_cache = response_cache or InMemoryTTLCache(ttl_seconds=60)
        self.data_circuit_breaker = data_circuit_breaker or CircuitBreaker(
            name="data-service"
        )
        self.llm_circuit_breaker = llm_circuit_breaker or CircuitBreaker(
            name="llm-service"
        )
        self.data_timeout_seconds = data_timeout_seconds
        self.llm_timeout_seconds = llm_timeout_seconds
        self.retry_attempts = retry_attempts

    def run(self, user_input: str) -> dict[str, object]:
        normalized_input, simulation_scenarios = self._extract_simulation_scenarios(
            user_input
        )
        simulation_enabled = bool(simulation_scenarios)
        trace_id = str(uuid4())
        request_started_at = perf_counter()
        steps: list[dict[str, object]] = []
        fallback_used = False
        response_source = "generated"
        data_source = "database"

        response_key = f"response:{normalized_input.strip().lower()}"
        cached_response = None
        if not simulation_enabled:
            cached_response = self.response_cache.get(response_key)

        if cached_response is not None:
            response_source = "response-cache"
            metadata = self._build_metadata(
                trace_id=trace_id,
                request_started_at=request_started_at,
                steps=steps,
                fallback_used=fallback_used,
                response_source=response_source,
                data_source="not-used",
                cache_status={"response_cache": "hit", "data_cache": "not-used"},
                intent=None,
                simulation_scenarios=simulation_scenarios,
            )
            return self.response_builder.build(cached_response, metadata)

        query_plan = self._run_step(
            step_name="query-plan",
            steps=steps,
            executor=lambda: self.query_service.build_query(normalized_input),
        )
        data_key = (
            f"data:{query_plan.intent}:{query_plan.entity}:"
            f"{query_plan.operation}:{query_plan.limit}"
        )

        data = None
        data_cache_status = "miss"
        if not simulation_enabled:
            data = self.data_cache.get(data_key)
            data_cache_status = "hit" if data is not None else "miss"
        else:
            data_cache_status = "bypass-simulation"

        if data is None:
            try:
                data = self._run_with_resilience(
                    breaker=self.data_circuit_breaker,
                    timeout_seconds=self.data_timeout_seconds,
                    steps=steps,
                    step_name="data-fetch",
                    executor=lambda: self._execute_data_step(
                        query_plan,
                        simulation_scenarios,
                    ),
                )
                if not simulation_enabled:
                    self.data_cache.set(data_key, data)
            except RuntimeError:
                fallback_used = True
                response_source = "fallback"
                fallback_text = self._run_step(
                    step_name="data-fallback",
                    steps=steps,
                    executor=lambda: self.llm_service.generate_fallback_text(
                        normalized_input,
                        None,
                    ),
                )
                metadata = self._build_metadata(
                    trace_id=trace_id,
                    request_started_at=request_started_at,
                    steps=steps,
                    fallback_used=fallback_used,
                    response_source=response_source,
                    data_source="unavailable",
                    cache_status={
                        "response_cache": (
                            "bypass-simulation" if simulation_enabled else "miss"
                        ),
                        "data_cache": data_cache_status,
                    },
                    intent=getattr(query_plan, "intent", None),
                    simulation_scenarios=simulation_scenarios,
                )
                logger.warning(
                    "copilot_request_data_fallback", extra={"metadata": metadata}
                )
                return self.response_builder.build(fallback_text, metadata)
        else:
            data_source = "data-cache"
            steps.append(
                {"step": "data-fetch", "status": "cache-hit", "duration_ms": 0.0}
            )

        try:
            generated_text = self._run_with_resilience(
                breaker=self.llm_circuit_breaker,
                timeout_seconds=self.llm_timeout_seconds,
                steps=steps,
                step_name="llm-generate",
                executor=lambda: self._execute_llm_step(
                    normalized_input,
                    data,
                    simulation_scenarios,
                ),
            )
        except RuntimeError:
            fallback_used = True
            response_source = "fallback"
            generated_text = self._run_step(
                step_name="llm-fallback",
                steps=steps,
                executor=lambda: self.llm_service.generate_fallback_text(
                    normalized_input,
                    data,
                ),
            )

        if not simulation_enabled:
            self.response_cache.set(response_key, generated_text)
        metadata = self._build_metadata(
            trace_id=trace_id,
            request_started_at=request_started_at,
            steps=steps,
            fallback_used=fallback_used,
            response_source=response_source,
            data_source=data_source,
            cache_status={
                "response_cache": "bypass-simulation" if simulation_enabled else "miss",
                "data_cache": data_cache_status,
            },
            intent=getattr(query_plan, "intent", None),
            simulation_scenarios=simulation_scenarios,
        )
        logger.info("copilot_request_completed", extra={"metadata": metadata})
        return self.response_builder.build(generated_text, metadata)

    def _extract_simulation_scenarios(self, user_input: str) -> tuple[str, list[str]]:
        normalized_input = user_input
        scenarios: list[str] = []

        for marker, scenario in self.SIMULATION_MARKERS.items():
            if marker in normalized_input:
                normalized_input = normalized_input.replace(marker, " ")
                scenarios.append(scenario)

        return normalized_input.strip(), scenarios

    def _execute_data_step(
        self,
        query_plan,
        simulation_scenarios: list[str],
    ) -> dict[str, object]:
        if "data-error" in simulation_scenarios:
            raise RuntimeError("simulated data service error")

        if "data-timeout" in simulation_scenarios:
            sleep(self.data_timeout_seconds + 0.05)

        return self.data_service.fetch_data(query_plan)

    def _execute_llm_step(
        self,
        user_input: str,
        data: dict[str, object],
        simulation_scenarios: list[str],
    ) -> str:
        if "llm-error" in simulation_scenarios:
            raise RuntimeError("simulated llm service error")

        if "llm-timeout" in simulation_scenarios:
            sleep(self.llm_timeout_seconds + 0.05)

        return self.llm_service.generate_text(user_input, data)

    def _run_step(self, step_name: str, steps: list[dict[str, object]], executor):
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

    def _run_with_resilience(
        self,
        breaker: CircuitBreaker,
        timeout_seconds: float,
        steps: list[dict[str, object]],
        step_name: str,
        executor,
    ):
        last_error: Exception | None = None

        for attempt in range(1, self.retry_attempts + 1):
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
            ) as error:  # pragma: no cover - exercised in tests through failures
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

    def _build_metadata(
        self,
        trace_id: str,
        request_started_at: float,
        steps: list[dict[str, object]],
        fallback_used: bool,
        response_source: str,
        data_source: str,
        cache_status: dict[str, str],
        intent: str | None,
        simulation_scenarios: list[str] | None = None,
    ) -> dict[str, object]:
        metadata: dict[str, object] = {
            "trace_id": trace_id,
            "intent": intent,
            "fallback_used": fallback_used,
            "response_source": response_source,
            "data_source": data_source,
            "cache": {
                **cache_status,
                "backend": self.data_cache.backend_name,
            },
            "circuit_breakers": {
                "data_service": self.data_circuit_breaker.snapshot().__dict__,
                "llm_service": self.llm_circuit_breaker.snapshot().__dict__,
            },
            "steps": steps,
            "total_duration_ms": round((perf_counter() - request_started_at) * 1000, 2),
        }

        if simulation_scenarios:
            metadata["simulation"] = {
                "enabled": True,
                "scenarios": simulation_scenarios,
            }

        return metadata
