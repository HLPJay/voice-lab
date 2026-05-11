import time
from uuid import uuid4

from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.context import get_request_id, request_id_var
from app.core.errors import VoiceLabError
from app.core.logging import get_logger

http_logger = get_logger("http")
_error_logger = get_logger("error_handler")


class RequestContextMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope: dict, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = "req_" + uuid4().hex[:12]
        request_id_var.set(request_id)

        path = scope.get("path", "")
        method = scope.get("method", "")

        skip_logging = path in ("/health",) or path.startswith("/static/")

        if not skip_logging:
            http_logger.info(
                "request_start",
                extra={
                    "method": method,
                    "path": path,
                    "request_id": request_id,
                },
            )

        start = time.monotonic()
        response_started = False

        async def send_wrapper(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                # Inject X-Request-ID into response headers
                headers = dict(message.get("headers", []))
                headers[b"x-request-id"] = request_id.encode()
                message = {**message, "headers": list(headers.items())}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            duration_ms = round((time.monotonic() - start) * 1000)

            if isinstance(exc, VoiceLabError):
                _error_logger.warning(
                    "voice_lab_error",
                    extra={
                        "error_code": exc.code,
                        "error_message": exc.message,
                        "status_code": exc.status_code,
                        "path": path,
                        "method": method,
                        "job_id": exc.job_id,
                    },
                )
                payload = {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "detail": exc.detail,
                        "job_id": exc.job_id,
                    }
                }
                body = JSONResponse(content=payload, status_code=exc.status_code)
                await send_wrapper(
                    {
                        "type": "http.response.start",
                        "status": body.status_code,
                        "headers": [[b"content-type", b"application/json"]],
                    }
                )
                import json
                await send_wrapper({"type": "http.response.body", "body": json.dumps(payload).encode()})
                return

            if isinstance(exc, RequestValidationError):
                _error_logger.warning(
                    "validation_error",
                    extra={
                        "error_code": "VALIDATION_ERROR",
                        "path": path,
                        "method": method,
                        "error_count": len(exc.errors()),
                    },
                )
                payload = {
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "Request validation failed",
                        "detail": exc.errors(),
                        "job_id": None,
                    }
                }
                await send_wrapper(
                    {
                        "type": "http.response.start",
                        "status": 422,
                        "headers": [[b"content-type", b"application/json"]],
                    }
                )
                import json
                await send_wrapper({"type": "http.response.body", "body": json.dumps(payload).encode()})
                return

            # Unhandled exception
            _error_logger.error(
                "unhandled_error",
                extra={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc)[:500],
                    "path": path,
                    "method": method,
                },
            )
            if not response_started:
                response_body = b'{"error":{"code":"INTERNAL_ERROR","message":"Internal server error","detail":null,"job_id":null}}'
                await send(
                    {
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [
                            [b"content-type", b"application/json"],
                            [b"x-request-id", request_id.encode()],
                        ],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": response_body,
                    }
                )
        else:
            # Normal completion — response already sent by send_wrapper
            pass
