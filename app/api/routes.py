from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.orchestrator.orchestrator import Orchestrator
from app.utils.database import check_database_connection
from app.utils.errors import INTERNAL_ERROR, descriptor_to_metadata

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
    is_connected, detail = check_database_connection()
    status = "ok" if is_connected else "unavailable"
    return {"status": status, "detail": detail}


@router.post("/copilot/question", response_model=CopilotQuestionResponse)
async def copilot_question(payload: CopilotQuestionRequest) -> CopilotQuestionResponse:
    try:
        result = orchestrator.run(payload.question)
        return CopilotQuestionResponse(
            answer=str(result["message"]),
            metadata=dict(result.get("metadata", {})),
        )
    except Exception:
        return CopilotQuestionResponse(
            answer=INTERNAL_ERROR.user_message,
            metadata={
                "fallback_used": True,
                "response_source": "friendly-error",
                "error": descriptor_to_metadata(INTERNAL_ERROR),
            },
        )
