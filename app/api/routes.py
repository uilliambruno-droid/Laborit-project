from fastapi import APIRouter

from app.utils.database import check_database_connection

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/database")
async def database_health_check() -> dict[str, str]:
    is_connected, detail = check_database_connection()
    status = "ok" if is_connected else "unavailable"
    return {"status": status, "detail": detail}
