import asyncio
import functools

from app.core.logging import get_logger

_retry_logger = get_logger("retry")


def async_retry(
    max_attempts: int = 3,
    backoff_base: float = 1.0,
    retryable_exceptions: tuple = (),
    retryable_status_codes: tuple = (502, 503, 504),
):
    """Decorator for async functions with exponential backoff retry."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    if hasattr(result, 'status_code') and result.status_code in retryable_status_codes:
                        if attempt < max_attempts:
                            wait = backoff_base * (2 ** (attempt - 1))
                            _retry_logger.warning(
                                "retry_status_code",
                                extra={
                                    "attempt": attempt,
                                    "max_attempts": max_attempts,
                                    "status_code": result.status_code,
                                    "wait_seconds": wait,
                                    "function": func.__name__,
                                },
                            )
                            await asyncio.sleep(wait)
                            continue
                    return result
                except retryable_exceptions as exc:
                    last_exception = exc
                    if attempt < max_attempts:
                        wait = backoff_base * (2 ** (attempt - 1))
                        _retry_logger.warning(
                            "retry_exception",
                            extra={
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "error_type": type(exc).__name__,
                                "error_message": str(exc)[:200],
                                "wait_seconds": wait,
                                "function": func.__name__,
                            },
                        )
                        await asyncio.sleep(wait)
                    else:
                        _retry_logger.error(
                            "retry_exhausted",
                            extra={
                                "attempts": max_attempts,
                                "error_type": type(exc).__name__,
                                "function": func.__name__,
                            },
                        )
                        raise
            return result
        return wrapper
    return decorator
