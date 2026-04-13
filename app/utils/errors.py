from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorDescriptor:
    code: str
    source: str
    user_message: str
    retriable: bool
    category: str


@dataclass(frozen=True)
class StepExecutionError(RuntimeError):
    step_name: str
    reason: str
    source: str
    retriable: bool


QUERY_PLAN_ERROR = ErrorDescriptor(
    code="QUERY_PLAN_ERROR",
    source="query_service",
    user_message=(
        "I could not interpret this question safely right now. "
        "Please try rephrasing it with more business context."
    ),
    retriable=True,
    category="validation",
)

DATA_TIMEOUT_ERROR = ErrorDescriptor(
    code="DATA_TIMEOUT",
    source="data_service",
    user_message=(
        "I am temporarily unable to retrieve data in time. "
        "Please try again in a few seconds."
    ),
    retriable=True,
    category="timeout",
)

DATA_CIRCUIT_OPEN_ERROR = ErrorDescriptor(
    code="DATA_CIRCUIT_OPEN",
    source="data_service",
    user_message=(
        "Our data source is temporarily unstable, so this request was degraded. "
        "Please retry shortly."
    ),
    retriable=True,
    category="resilience",
)

DATA_SERVICE_ERROR = ErrorDescriptor(
    code="DATA_SERVICE_ERROR",
    source="data_service",
    user_message=(
        "I could not retrieve the required data right now, but your request was processed."
    ),
    retriable=True,
    category="dependency",
)

LLM_TIMEOUT_ERROR = ErrorDescriptor(
    code="LLM_TIMEOUT",
    source="llm_service",
    user_message=(
        "The response generation took too long. "
        "Please try again for a richer answer."
    ),
    retriable=True,
    category="timeout",
)

LLM_CIRCUIT_OPEN_ERROR = ErrorDescriptor(
    code="LLM_CIRCUIT_OPEN",
    source="llm_service",
    user_message=(
        "The generation service is temporarily unstable. "
        "A simplified response was returned."
    ),
    retriable=True,
    category="resilience",
)

LLM_SERVICE_ERROR = ErrorDescriptor(
    code="LLM_SERVICE_ERROR",
    source="llm_service",
    user_message=(
        "I could not generate the full answer right now, but I returned a safe summary."
    ),
    retriable=True,
    category="dependency",
)

FALLBACK_GENERATION_ERROR = ErrorDescriptor(
    code="FALLBACK_GENERATION_ERROR",
    source="llm_service",
    user_message=(
        "I could not generate a detailed answer at the moment. "
        "Please retry in a few seconds."
    ),
    retriable=True,
    category="fallback",
)

INTERNAL_ERROR = ErrorDescriptor(
    code="INTERNAL_ERROR",
    source="orchestrator",
    user_message=(
        "We had an internal processing issue and returned a safe response. "
        "Please retry shortly."
    ),
    retriable=True,
    category="internal",
)


def descriptor_to_metadata(descriptor: ErrorDescriptor) -> dict[str, object]:
    return {
        "code": descriptor.code,
        "source": descriptor.source,
        "category": descriptor.category,
        "retriable": descriptor.retriable,
    }


def map_step_error(error: StepExecutionError) -> ErrorDescriptor:
    if error.source == "data_service":
        if error.reason == "timeout":
            return DATA_TIMEOUT_ERROR
        if error.reason == "circuit_open":
            return DATA_CIRCUIT_OPEN_ERROR
        return DATA_SERVICE_ERROR

    if error.source == "llm_service":
        if error.reason == "timeout":
            return LLM_TIMEOUT_ERROR
        if error.reason == "circuit_open":
            return LLM_CIRCUIT_OPEN_ERROR
        return LLM_SERVICE_ERROR

    return INTERNAL_ERROR
