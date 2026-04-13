from fastapi import FastAPI

from app.api.routes import router as api_router
from app.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


def create_app() -> FastAPI:
    setup_logging()
    application = FastAPI(
        title="Laborit Project API",
        version="0.1.0",
        description="Initial API foundation for solution development.",
    )
    application.include_router(api_router)
    logger.info("application_startup", version="0.1.0")
    return application


app = create_app()
