from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Session, select

from app.core.time import utc_now_iso
from app.models.provider_call_log import ProviderCallLog


def test_call_log_model_creation():
    """ProviderCallLog 模型可正常创建实例"""
    entry = ProviderCallLog(
        id="calllog_test123",
        request_id="req_abc123",
        job_id="job_xyz",
        provider="minimax",
        api_path="/v1/t2a_v2",
        method="POST",
        status_code=200,
        duration_ms=1234,
        error_type=None,
        error_message=None,
        created_at=utc_now_iso(),
    )
    assert entry.id == "calllog_test123"
    assert entry.request_id == "req_abc123"
    assert entry.job_id == "job_xyz"
    assert entry.provider == "minimax"
    assert entry.api_path == "/v1/t2a_v2"
    assert entry.method == "POST"
    assert entry.status_code == 200
    assert entry.duration_ms == 1234
    assert entry.error_type is None
    assert entry.error_message is None


def test_call_log_table_created(temp_db):
    """provider_call_logs 表在建表时被创建"""
    engine, _ = temp_db
    # Verify table exists by querying it
    with Session(engine) as session:
        result = session.exec(select(ProviderCallLog).limit(1))
        assert result.all() == []  # empty is fine, table exists


def test_sync_render_creates_no_call_log_for_mock(test_app, seed_mock_binding, temp_db):
    """Mock provider 的 sync render 不产生 call_log（只有 MiniMax 才写）"""
    engine, _ = temp_db
    from fastapi.testclient import TestClient

    client = TestClient(test_app)
    resp = client.post(
        "/api/voice/render",
        json={"text": "test", "provider": "mock"},
    )
    assert resp.status_code == 200

    with Session(engine) as session:
        logs = session.exec(select(ProviderCallLog)).all()
        assert len(logs) == 0


@pytest.mark.asyncio
async def test_minimax_request_creates_call_log(temp_db):
    """MiniMax adapter._request() 写入 call_log"""
    engine, _ = temp_db

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"base_resp": {"status_code": 0}}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.request = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_instance

        with patch("app.core.database.get_engine", return_value=engine):
            from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

            adapter = MiniMaxSpeechAdapter()
            await adapter._request("POST", "/v1/t2a_v2", json={"text": "hello"})

    with Session(engine) as session:
        logs = session.exec(select(ProviderCallLog)).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.provider == "minimax"
        assert log.api_path == "/v1/t2a_v2"
        assert log.method == "POST"
        assert log.status_code == 200
        assert log.duration_ms is not None
        assert log.duration_ms >= 0


@pytest.mark.asyncio
async def test_call_log_on_error(temp_db):
    """异常时也写入 call_log，包含 error_type 和 error_message"""
    engine, _ = temp_db

    import httpx

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.request = AsyncMock(side_effect=httpx.TimeoutException("connection timeout"))
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_instance

        with patch("app.core.database.get_engine", return_value=engine):
            from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

            adapter = MiniMaxSpeechAdapter()
            with pytest.raises(httpx.TimeoutException):
                await adapter._request("POST", "/v1/t2a_v2", json={"text": "hello"})

    with Session(engine) as session:
        logs = session.exec(select(ProviderCallLog)).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.status_code is None
        assert log.error_type == "TimeoutException"
        assert "timeout" in log.error_message


@pytest.mark.asyncio
async def test_call_log_error_message_truncated(temp_db):
    """error_message 超过 500 字符时被截断"""
    engine, _ = temp_db

    long_message = "A" * 600

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.request = AsyncMock(side_effect=RuntimeError(long_message))
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_instance

        with patch("app.core.database.get_engine", return_value=engine):
            from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

            adapter = MiniMaxSpeechAdapter()
            with pytest.raises(RuntimeError):
                await adapter._request("POST", "/v1/t2a_v2", json={})

    with Session(engine) as session:
        logs = session.exec(select(ProviderCallLog)).all()
        assert len(logs) == 1
        log = logs[0]
        assert len(log.error_message) == 500


@pytest.mark.asyncio
async def test_call_log_includes_request_id(temp_db):
    """call_log 包含 request_id"""
    engine, _ = temp_db

    from app.core.context import request_id_var

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"base_resp": {"status_code": 0}}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_instance = AsyncMock()
        mock_instance.request = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_instance

        with patch("app.core.database.get_engine", return_value=engine):
            from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

            request_id_var.set("req_testcontext123")

            adapter = MiniMaxSpeechAdapter()
            await adapter._request("POST", "/v1/get_voice", json={"voice_type": "all"})

    with Session(engine) as session:
        logs = session.exec(select(ProviderCallLog)).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.request_id == "req_testcontext123"
