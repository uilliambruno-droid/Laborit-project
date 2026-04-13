from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.orchestrator.orchestrator import Orchestrator
from app.utils.database import check_database_connection
from app.utils.logger import get_logger

router = APIRouter(prefix="/api", tags=["api"])
orchestrator = Orchestrator()
logger = get_logger(__name__)


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
    is_connected, detail = check_database_connection()
    status = "ok" if is_connected else "unavailable"
    return {"status": status, "detail": detail}


@router.post("/copilot/question", response_model=CopilotQuestionResponse)
async def copilot_question(payload: CopilotQuestionRequest) -> CopilotQuestionResponse:
    logger.info(
        "copilot_request_received",
        question_length=len(payload.question),
        question_preview=payload.question[:80],
    )
    result = orchestrator.run(payload.question)
    response = CopilotQuestionResponse(
        answer=str(result["message"]),
        metadata=dict(result.get("metadata", {})),
    )
    logger.info(
        "copilot_request_done",
        trace_id=response.metadata.get("trace_id"),
        response_source=response.metadata.get("response_source"),
        fallback_used=response.metadata.get("fallback_used"),
        total_duration_ms=response.metadata.get("total_duration_ms"),
        answer_length=len(response.answer),
    )
    return response
