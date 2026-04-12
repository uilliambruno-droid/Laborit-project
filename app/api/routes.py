from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.orchestrator.orchestrator import Orchestrator

router = APIRouter(prefix="/api", tags=["api"])
orchestrator = Orchestrator()


class CopilotQuestionRequest(BaseModel):
    question: str = Field(
        min_length=3, description="Manager question for the commercial copilot"
    )


class CopilotQuestionResponse(BaseModel):
    answer: str


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/copilot/question", response_model=CopilotQuestionResponse)
async def ask_copilot(payload: CopilotQuestionRequest) -> CopilotQuestionResponse:
    result = orchestrator.run(payload.question)
    return CopilotQuestionResponse(answer=result["message"])
