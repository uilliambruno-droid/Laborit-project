from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router as api_router
from app.i18n import VALIDATION_PAYLOAD_MESSAGE, get_validation_messages
from app.utils.metrics import metrics_registry


def _map_friendly_message(error_type: str, message: str) -> tuple[str, str]:
    return get_validation_messages(error_type=error_type, raw_message=message)


async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors: list[dict[str, str]] = []
    for raw_error in exc.errors():
        raw_loc = raw_error.get("loc", [])
        field = ".".join(str(item) for item in raw_loc if item != "body") or "body"
        message_en, message_pt = _map_friendly_message(
            str(raw_error.get("type", "")),
            str(raw_error.get("msg", "")),
        )
        errors.append(
            {
                "field": field,
                "message": message_en,
                "message_pt": message_pt,
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "message": VALIDATION_PAYLOAD_MESSAGE["en"],
            "message_pt": VALIDATION_PAYLOAD_MESSAGE["pt"],
            "errors": errors,
        },
    )


def create_app() -> FastAPI:
    application = FastAPI(
        title="Laborit Project API",
        version="0.1.0",
        description="Initial API foundation for solution development.",
    )

    @application.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        started_at = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - started_at) * 1000
        metrics_registry.record_http(
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    application.include_router(api_router)
    return application


app = create_app()
