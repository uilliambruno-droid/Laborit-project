from logging import getLogger
from time import perf_counter
from uuid import uuid4

from app.builder.response_builder import ResponseBuilder
from app.orchestrator.metadata import build_request_metadata
from app.orchestrator.resilience import run_step, run_with_resilience
from app.services.data_service import DataService
from app.services.llm_service import LLMService
from app.services.query_service import QueryService
from app.utils.cache import InMemoryTTLCache
from app.utils.circuit_breaker import CircuitBreaker

logger = getLogger(__name__)


class Orchestrator:
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
        trace_id = str(uuid4())
        request_started_at = perf_counter()
        steps: list[dict[str, object]] = []
        fallback_used = False
        response_source = "generated"
        data_source = "database"

        response_key = f"response:{user_input.strip().lower()}"
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
            )
            return self.response_builder.build(cached_response, metadata)

        query_plan = self._run_step(
            step_name="query-plan",
            steps=steps,
            executor=lambda: self.query_service.build_query(user_input),
        )
        data_key = query_plan.data_cache_key()

        data = self.data_cache.get(data_key)
        data_cache_status = "hit" if data is not None else "miss"
        if data is None:
            try:
                data = self._run_with_resilience(
                    breaker=self.data_circuit_breaker,
                    timeout_seconds=self.data_timeout_seconds,
                    steps=steps,
                    step_name="data-fetch",
                    executor=lambda: self.data_service.fetch_data(query_plan),
                )
                data = self._normalize_data_payload(data)
                self.data_cache.set(data_key, data)
            except RuntimeError:
                fallback_used = True
                response_source = "fallback"
                fallback_text = self._run_step(
                    step_name="data-fallback",
                    steps=steps,
                    executor=lambda: self.llm_service.generate_fallback_text(
                        user_input,
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
                        "response_cache": "miss",
                        "data_cache": data_cache_status,
                    },
                    intent=query_plan.intent.value,
                )
                logger.warning(
                    "copilot_request_data_fallback", extra={"metadata": metadata}
                )
                return self.response_builder.build(fallback_text, metadata)
        else:
            data = self._normalize_data_payload(data)
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
                executor=lambda: self.llm_service.generate_text(user_input, data),
            )
        except RuntimeError:
            fallback_used = True
            response_source = "fallback"
            generated_text = self._run_step(
                step_name="llm-fallback",
                steps=steps,
                executor=lambda: self.llm_service.generate_fallback_text(
                    user_input, data
                ),
            )

        self.response_cache.set(response_key, generated_text)
        metadata = self._build_metadata(
            trace_id=trace_id,
            request_started_at=request_started_at,
            steps=steps,
            fallback_used=fallback_used,
            response_source=response_source,
            data_source=data_source,
            cache_status={"response_cache": "miss", "data_cache": data_cache_status},
            intent=query_plan.intent.value,
        )
        logger.info("copilot_request_completed", extra={"metadata": metadata})
        return self.response_builder.build(generated_text, metadata)

    def _normalize_data_payload(self, payload: dict[str, object]) -> dict[str, object]:
        intent = payload.get("intent")
        if hasattr(intent, "value"):
            normalized = dict(payload)
            normalized["intent"] = str(getattr(intent, "value"))
            return normalized
        return payload

    def _run_step(self, step_name: str, steps: list[dict[str, object]], executor):
        return run_step(step_name=step_name, steps=steps, executor=executor)

    def _run_with_resilience(
        self,
        breaker: CircuitBreaker,
        timeout_seconds: float,
        steps: list[dict[str, object]],
        step_name: str,
        executor,
    ):
        return run_with_resilience(
            breaker=breaker,
            timeout_seconds=timeout_seconds,
            retry_attempts=self.retry_attempts,
            steps=steps,
            step_name=step_name,
            executor=executor,
        )

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
    ) -> dict[str, object]:
        return build_request_metadata(
            trace_id=trace_id,
            request_started_at=request_started_at,
            steps=steps,
            fallback_used=fallback_used,
            response_source=response_source,
            data_source=data_source,
            cache_status=cache_status,
            cache_backend=self.data_cache.backend_name,
            data_breaker_snapshot=self.data_circuit_breaker.snapshot().__dict__,
            llm_breaker_snapshot=self.llm_circuit_breaker.snapshot().__dict__,
            intent=intent,
        )
