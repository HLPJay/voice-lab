from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

_error_logger = get_logger("error_handler")


class VoiceLabError(Exception):
    status_code = 400
    code = "VOICE_LAB_ERROR"

    def __init__(self, message: str, detail: str | None = None, job_id: str | None = None):
        self.message = message
        self.detail = detail
        self.job_id = job_id


class ValidationError(VoiceLabError):
    status_code = 422
    code = "VALIDATION_ERROR"


class ProfileNotFound(VoiceLabError):
    status_code = 404
    code = "PROFILE_NOT_FOUND"


class BindingNotFound(VoiceLabError):
    status_code = 404
    code = "BINDING_NOT_FOUND"


class UnsupportedProvider(VoiceLabError):
    status_code = 400
    code = "UNSUPPORTED_PROVIDER"


class ProviderNotConfigured(VoiceLabError):
    code = "PROVIDER_NOT_CONFIGURED"


class ProviderError(VoiceLabError):
    code = "PROVIDER_ERROR"


class JobNotFound(VoiceLabError):
    status_code = 404
    code = "JOB_NOT_FOUND"


class AssetNotFound(VoiceLabError):
    status_code = 404
    code = "ASSET_NOT_FOUND"


async def voice_lab_error_handler(request: Request, exc: VoiceLabError) -> JSONResponse:
    _error_logger.warning(
        "voice_lab_error",
        extra={
            "error_code": exc.code,
            "error_message": exc.message,
            "error_detail": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "job_id": exc.job_id,
        },
    )
    payload = {"error": {"code": exc.code, "message": exc.message, "detail": exc.detail, "job_id": exc.job_id}}
    return JSONResponse(status_code=exc.status_code, content=payload)


async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Sanitize errors: Pydantic v2 may include raw exception objects in ctx, which
    # are not JSON-serializable. Strip ctx to ensure safe serialization.
    errors = []
    for err in exc.errors():
        clean = {k: v for k, v in err.items() if k != "ctx"}
        errors.append(clean)

    _error_logger.warning(
        "validation_error",
        extra={
            "error_code": "VALIDATION_ERROR",
            "path": request.url.path,
            "method": request.method,
            "error_count": len(errors),
        },
    )
    payload = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "detail": errors,
            "job_id": None,
        }
    }
    return JSONResponse(status_code=422, content=payload)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    _error_logger.error(
        "unhandled_error",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc)[:500],
            "path": request.url.path,
            "method": request.method,
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "detail": None,
                "job_id": None,
            }
        },
    )
