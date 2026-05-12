import logging
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.logging import get_logger


def test_provider_logger_exists():
    """provider.minimax logger 可正常创建"""
    logger = get_logger("provider.minimax")
    assert logger.name == "provider.minimax"
    assert isinstance(logger, logging.Logger)


def test_sync_render_produces_provider_logs(test_app, seed_mock_binding, caplog):
    """同步渲染调用 mock provider 时不产生 provider_request 日志（mock 不经过 _request）"""
    from fastapi.testclient import TestClient

    caplog.set_level(logging.INFO)
    client = TestClient(test_app)
    resp = client.post(
        "/api/voice/render",
        json={"text": "test", "provider": "mock"},
    )
    assert resp.status_code == 200

    provider_request_msgs = [
        rec.message for rec in caplog.records if rec.message == "provider_request"
    ]
    assert len(provider_request_msgs) == 0, "mock provider should not produce provider_request logs"


@pytest.mark.asyncio
async def test_request_method_logs_format(caplog):
    """验证 _request 方法的日志格式"""
    caplog.set_level(logging.DEBUG)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"base_resp": {"status_code": 0}}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client_instance

        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

        adapter = MiniMaxSpeechAdapter()
        await adapter._request("POST", "/v1/t2a_v2", json={"text": "hello"})

    records = caplog.records
    messages = [rec.message for rec in records]

    assert "provider_request" in messages, f"Expected provider_request in {messages}"
    assert "provider_response" in messages, f"Expected provider_response in {messages}"

    request_records = [rec for rec in records if rec.message == "provider_request"]
    response_records = [rec for rec in records if rec.message == "provider_response"]

    assert request_records[0].provider == "minimax"
    assert request_records[0].method == "POST"
    assert request_records[0].path == "/v1/t2a_v2"

    assert response_records[0].provider == "minimax"
    assert response_records[0].method == "POST"
    assert response_records[0].path == "/v1/t2a_v2"
    assert response_records[0].status_code == 200
    assert hasattr(response_records[0], "duration_ms")


@pytest.mark.asyncio
async def test_request_method_logs_error_on_timeout(caplog):
    """超时时产生 provider_error 日志"""
    caplog.set_level(logging.ERROR)

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(side_effect=httpx.TimeoutException("connection timeout"))
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client_instance

        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

        adapter = MiniMaxSpeechAdapter()
        with pytest.raises(httpx.TimeoutException):
            await adapter._request("POST", "/v1/t2a_v2", json={"text": "hello"})

    records = caplog.records
    messages = [rec.message for rec in records]

    assert "provider_error" in messages, f"Expected provider_error in {messages}"

    error_records = [rec for rec in records if rec.message == "provider_error"]
    assert error_records[0].provider == "minimax"
    assert error_records[0].method == "POST"
    assert error_records[0].path == "/v1/t2a_v2"
    assert error_records[0].error_type == "TimeoutException"
    assert hasattr(error_records[0], "duration_ms")


@pytest.mark.asyncio
async def test_no_auth_header_in_logs(caplog):
    """日志中不包含 Authorization header"""
    caplog.set_level(logging.DEBUG)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"base_resp": {"status_code": 0}}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client_instance = AsyncMock()
        mock_client_instance.request = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client_instance

        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

        adapter = MiniMaxSpeechAdapter()
        await adapter._request("POST", "/v1/get_voice", json={"voice_type": "all"})

    all_logs = "\n".join(rec.message + " " + str(rec.__dict__.get("extra", "")) for rec in caplog.records)

    assert "Bearer" not in all_logs, "Authorization header value should not appear in logs"
    assert "replace_me" not in all_logs, "API key placeholder should not appear in logs"
    assert "MINIMAX_API_KEY" not in all_logs, "API key env var name should not appear in logs"
