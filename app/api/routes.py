from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.concurrency import run_in_threadpool

from app.orchestrator.orchestrator import Orchestrator
from app.utils.database import check_database_connection
from app.utils.metrics import metrics_registry
from app.utils.security import require_api_key

router = APIRouter(prefix="/api", tags=["api"])
orchestrator = Orchestrator()


class CopilotQuestionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Question made by portfolio manager to the commercial copilot",
    )

    @field_validator("question")
    @classmethod
    def validate_question_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("question cannot be blank")
        if normalized.count("?") > 3:
            raise ValueError("question contains too many consecutive question marks")
        return normalized


class CopilotQuestionResponse(BaseModel):
    answer: str
    metadata: dict[str, object]


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/database")
async def database_health_check() -> dict[str, str]:
    is_connected, detail = await run_in_threadpool(check_database_connection)
    status = "ok" if is_connected else "unavailable"
    return {"status": status, "detail": detail}


@router.get("/metrics", dependencies=[Depends(require_api_key)])
async def metrics_snapshot() -> dict[str, object]:
    return metrics_registry.snapshot()


@router.post("/copilot/question", response_model=CopilotQuestionResponse)
async def copilot_question(
    payload: CopilotQuestionRequest,
    _: None = Depends(require_api_key),
) -> CopilotQuestionResponse:
    result = await run_in_threadpool(orchestrator.run, payload.question)
    metadata = dict(result.get("metadata", {}))
    metrics_registry.record_copilot_metadata(metadata)
    return CopilotQuestionResponse(
        answer=str(result["message"]),
        metadata=metadata,
    )
