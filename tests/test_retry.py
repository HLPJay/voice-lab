import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.retry import async_retry


# ── Decorator unit tests ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_retry_succeeds_first_attempt():
    """First attempt succeeds — no retry."""

    @async_retry(max_attempts=3, retryable_exceptions=(ValueError,))
    async def succeed():
        return "ok"

    result = await succeed()
    assert result == "ok"


@pytest.mark.asyncio
async def test_retry_succeeds_after_exception():
    """First attempt raises retryable exception, second succeeds."""

    call_count = 0

    @async_retry(max_attempts=3, backoff_base=0.01, retryable_exceptions=(ValueError,))
    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("transient")
        return "ok"

    result = await flaky()
    assert result == "ok"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_raises():
    """All attempts raise —最终抛出原始异常."""

    call_count = 0

    @async_retry(max_attempts=3, backoff_base=0.01, retryable_exceptions=(ValueError,))
    async def always_fail():
        nonlocal call_count
        call_count += 1
        raise ValueError("permanent")

    with pytest.raises(ValueError, match="permanent"):
        await always_fail()

    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_non_retryable_exception_no_retry():
    """Non-whitelisted exception is not retried."""

    call_count = 0

    @async_retry(max_attempts=3, retryable_exceptions=(ValueError,))
    async def bad_input():
        nonlocal call_count
        call_count += 1
        raise TypeError("not allowed")

    with pytest.raises(TypeError, match="not allowed"):
        await bad_input()

    assert call_count == 1  # No retry


@pytest.mark.asyncio
async def test_retry_on_502_status():
    """502 response triggers retry and succeeds on second attempt."""

    call_count = 0

    class FakeResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    @async_retry(max_attempts=3, backoff_base=0.01, retryable_status_codes=(502, 503, 504))
    async def flaky_status():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return FakeResponse(502)
        return FakeResponse(200)

    result = await flaky_status()
    assert result.status_code == 200
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_backoff_timing():
    """Retry intervals follow exponential backoff: 1s → 2s."""

    sleeps = []

    real_sleep = asyncio.sleep

    async def mock_sleep(delay):
        sleeps.append(delay)
        await real_sleep(0)  # no actual wait

    call_count = 0

    @async_retry(max_attempts=3, backoff_base=1.0, retryable_exceptions=(ValueError,))
    async def always_fail():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise ValueError("fail")
        return "ok"

    with patch("asyncio.sleep", mock_sleep):
        await always_fail()

    assert sleeps == [1.0, 2.0]  # backoff_base * 2^0, backoff_base * 2^1


# ── Adapter integration tests ────────────────────────────────────

class FakeResponse:
    """Minimal fake httpx.Response."""
    def __init__(self, status_code: int):
        self.status_code = status_code


@pytest.mark.asyncio
async def test_adapter_retries_on_timeout(caplog):
    """Adapter._request() retries on TimeoutException and succeeds."""
    from unittest.mock import AsyncMock, patch

    from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

    adapter = MiniMaxSpeechAdapter()

    call_count = 0

    async def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.TimeoutException("timed out")
        return FakeResponse(200)

    with patch("app.providers.minimax_speech_adapter.get_settings") as mock_settings, \
         patch("asyncio.sleep", AsyncMock()) as mock_sleep, \
         patch.object(adapter, "_save_call_log"):
        settings = MagicMock()
        settings.minimax_timeout_seconds = 120
        settings.provider_retry_max_attempts = 3
        settings.provider_retry_backoff_base = 0.01
        settings.minimax_api_key = "test-key"
        settings.minimax_base_url = "https://api.minimaxi.com"
        mock_settings.return_value = settings

        with patch("app.providers.minimax_speech_adapter.httpx.AsyncClient") as MockAsyncClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(side_effect=mock_request)
            MockAsyncClient.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            resp = await adapter._request("POST", "/v1/test")

    assert resp.status_code == 200
    assert call_count == 2
    warning_msgs = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert "retry_exception" in warning_msgs


@pytest.mark.asyncio
async def test_adapter_no_retry_on_400(caplog):
    """400 response does not trigger retry."""
    from unittest.mock import AsyncMock, patch

    from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

    adapter = MiniMaxSpeechAdapter()

    async def mock_request(*args, **kwargs):
        return FakeResponse(400)

    with patch("app.providers.minimax_speech_adapter.get_settings") as mock_settings, \
         patch("asyncio.sleep", AsyncMock()) as mock_sleep, \
         patch.object(adapter, "_save_call_log"):
        settings = MagicMock()
        settings.minimax_timeout_seconds = 120
        settings.provider_retry_max_attempts = 3
        settings.provider_retry_backoff_base = 0.01
        settings.minimax_api_key = "test-key"
        settings.minimax_base_url = "https://api.minimaxi.com"
        mock_settings.return_value = settings

        with patch("app.providers.minimax_speech_adapter.httpx.AsyncClient") as MockAsyncClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(side_effect=mock_request)
            MockAsyncClient.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            resp = await adapter._request("POST", "/v1/test")

    assert resp.status_code == 400
    warning_msgs = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert not any("retry" in m for m in warning_msgs)


@pytest.mark.asyncio
async def test_adapter_retry_502_then_200(caplog):
    """First 502 retry, second attempt returns 200."""
    from unittest.mock import AsyncMock, patch

    from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

    adapter = MiniMaxSpeechAdapter()

    responses = iter([FakeResponse(502), FakeResponse(200)])

    async def mock_request(*args, **kwargs):
        return next(responses)

    with patch("app.providers.minimax_speech_adapter.get_settings") as mock_settings, \
         patch("asyncio.sleep", AsyncMock()) as mock_sleep, \
         patch.object(adapter, "_save_call_log"):
        settings = MagicMock()
        settings.minimax_timeout_seconds = 120
        settings.provider_retry_max_attempts = 3
        settings.provider_retry_backoff_base = 0.01
        settings.minimax_api_key = "test-key"
        settings.minimax_base_url = "https://api.minimaxi.com"
        mock_settings.return_value = settings

        with patch("app.providers.minimax_speech_adapter.httpx.AsyncClient") as MockAsyncClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(side_effect=mock_request)
            MockAsyncClient.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            resp = await adapter._request("POST", "/v1/test")

    assert resp.status_code == 200
    warning_msgs = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert "retry_status_code" in warning_msgs


@pytest.mark.asyncio
async def test_adapter_audit_written_once(test_app):
    """Audit log written exactly once even after retries."""
    from unittest.mock import AsyncMock, patch

    from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

    adapter = MiniMaxSpeechAdapter()

    call_count = 0

    async def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.TimeoutException("timed out")
        return FakeResponse(200)

    save_log_calls = []

    def capture_save_log(**kwargs):
        save_log_calls.append(kwargs)

    with patch("app.providers.minimax_speech_adapter.get_settings") as mock_settings, \
         patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        settings = MagicMock()
        settings.minimax_timeout_seconds = 120
        settings.provider_retry_max_attempts = 3
        settings.provider_retry_backoff_base = 0.001
        settings.minimax_api_key = "test-key"
        settings.minimax_base_url = "https://api.minimaxi.com"
        mock_settings.return_value = settings

        with patch("app.providers.minimax_speech_adapter.httpx.AsyncClient") as MockAsyncClient:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(side_effect=mock_request)
            MockAsyncClient.return_value = mock_instance
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None

            with patch.object(adapter, "_save_call_log", side_effect=capture_save_log):
                resp = await adapter._request("POST", "/v1/test")

    assert resp.status_code == 200
    assert call_count == 2
    assert len(save_log_calls) == 1
    assert save_log_calls[0]["status_code"] == 200


