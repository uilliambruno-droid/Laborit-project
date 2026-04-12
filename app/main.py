from fastapi import FastAPI

from app.api.routes import router as api_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Laborit Project API",
        version="0.1.0",
        description="Initial API foundation for solution development.",
    )
    application.include_router(api_router)
    return application


app = create_app()
