from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
    code = "BINDING_NOT_FOUND"


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


async def voice_lab_error_handler(_: Request, exc: VoiceLabError) -> JSONResponse:
    payload = {"error": {"code": exc.code, "message": exc.message, "detail": exc.detail, "job_id": exc.job_id}}
    return JSONResponse(status_code=exc.status_code, content=payload)


async def request_validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    payload = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "detail": exc.errors(),
            "job_id": None,
        }
    }
    return JSONResponse(status_code=422, content=payload)
