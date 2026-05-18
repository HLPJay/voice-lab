"""
Minimal flat error response contract for XiangTa API.

Provides consistent error shape:
    {"ok": false, "errorKind": "...", "message": "...", "retryable": false}

Does NOT include: requestId, taskId, traceId, nested error, middleware.
"""
from fastapi.responses import JSONResponse


def error_body(
    *,
    error_kind: str,
    message: str,
    retryable: bool = False,
) -> dict:
    return {
        "ok": False,
        "errorKind": error_kind,
        "message": message,
        "retryable": retryable,
    }


def error_response(
    *,
    status_code: int,
    error_kind: str,
    message: str,
    retryable: bool = False,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(
            error_kind=error_kind,
            message=message,
            retryable=retryable,
        ),
    )