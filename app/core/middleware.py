import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.context import get_request_id, request_id_var
from app.core.logging import get_logger

http_logger = get_logger("http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = "req_" + uuid4().hex[:12]
        request_id_var.set(request_id)

        path = request.url.path
        method = request.method

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

        response = await call_next(request)

        duration_ms = round((time.monotonic() - start) * 1000)
        response.headers["X-Request-ID"] = request_id

        if not skip_logging:
            http_logger.info(
                "request_end",
                extra={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                },
            )

        return response
