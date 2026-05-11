import time
from uuid import uuid4

from starlette.requests import Request

from app.core.context import request_id_var
from app.core.logging import get_logger

http_logger = get_logger("http")


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

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Inject X-Request-ID into response headers
                headers = dict(message.get("headers", []))
                headers[b"x-request-id"] = request_id.encode()
                message = {**message, "headers": list(headers.items())}
            await send(message)

        await self.app(scope, receive, send_wrapper)

        if not skip_logging:
            duration_ms = round((time.monotonic() - start) * 1000)
            http_logger.info(
                "request_end",
                extra={
                    "method": method,
                    "path": path,
                    "request_id": request_id,
                    "duration_ms": duration_ms,
                },
            )
