"""
test_xiaomi_mimo_call_log.py

P16-V1-CLOSEOUT-XIAOMI-MIMO-CALL-LOG-AND-DAILY-ARCHIVE-D4-F3

Tests for XiaomiMiMoChatTTSAdapter ProviderCallLog write and
StatsService AudioAsset-only provider visibility.

No real API calls are made.
"""

import asyncio
import base64
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.provider_call_log import ProviderCallLog
from app.models.voice_asset import AudioAsset
from app.models.voice_job import VoiceJob
from app.services.stats_service import StatsService


# ── DB fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_engine():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()
    os.unlink(path)


# ── minimal valid WAV bytes for mock audio response ─────────────────────────

def _minimal_wav_base64() -> str:
    # 44-byte WAV header (PCM, 1 channel, 8000 Hz, 16-bit, 0 samples)
    import struct
    wav = (
        b"RIFF" + struct.pack("<I", 36) +
        b"WAVE" +
        b"fmt " + struct.pack("<I", 16) +
        struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16) +
        b"data" + struct.pack("<I", 0)
    )
    return base64.b64encode(wav).decode()


# ── adapter factory ──────────────────────────────────────────────────────────

def _make_adapter(http_client: httpx.AsyncClient):
    from app.providers.xiaomi_mimo_chat_tts_adapter import XiaomiMiMoChatTTSAdapter
    from app.domain.provider_config import ProviderConfig

    mock_provider_config = MagicMock(spec=ProviderConfig)
    mock_provider_config.name = "xiaomi_mimo"
    mock_provider_config.resolved_api_key = "test_api_key"
    mock_provider_config.resolved_base_url = "https://fake.xiaomi.test"
    mock_provider_config.default_model = None
    mock_provider_config.endpoints = None

    return XiaomiMiMoChatTTSAdapter(
        provider_config=mock_provider_config,
        http_client=http_client,
    )


# ── Test 1: HTTP 200 success writes ProviderCallLog ─────────────────────────

class TestCallLogOnSuccess:
    def test_successful_request_writes_call_log(self, tmp_engine):
        """HTTP 200 response must create one ProviderCallLog for xiaomi_mimo."""
        from app.domain.render_plan import RenderPlan

        audio_b64 = _minimal_wav_base64()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "id": "mimo_trace_001",
            "choices": [{"message": {"audio": {"data": audio_b64, "format": "wav"}}}],
            "usage": {"completion_tokens": 8},
        }

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=mock_response)

        adapter = _make_adapter(mock_client)

        plan = RenderPlan(
            id="job_test_001",
            text="你好世界",
            processed_text="你好世界",
            profile_id="profile_test",
            provider="xiaomi_mimo",
            provider_voice_id="mimo_voice_1",
            model="mimo-v2.5-tts",
        )

        with patch("app.core.database.get_engine", return_value=tmp_engine), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_request_id", return_value="req_abc"), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_job_id", return_value="job_test_001"), \
             patch("app.utils.files.storage_path", return_value=tempfile.mktemp(suffix=".wav")):
            asyncio.get_event_loop().run_until_complete(adapter.render_sync(plan))

        with Session(tmp_engine) as session:
            logs = list(session.exec(select(ProviderCallLog)).all())

        assert len(logs) == 1, f"Expected 1 call log, got {len(logs)}"
        log = logs[0]
        assert log.provider == "xiaomi_mimo"
        assert log.api_path == "/v1/chat/completions"
        assert log.method == "POST"
        assert log.status_code == 200
        assert log.duration_ms >= 0
        assert log.error_type is None
        assert log.error_message == "" or log.error_message is None

    def test_no_request_payload_or_audio_in_log(self, tmp_engine):
        """ProviderCallLog must not store request payload, response_json, or audio bytes."""
        from app.domain.render_plan import RenderPlan

        audio_b64 = _minimal_wav_base64()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "id": "trace_x",
            "choices": [{"message": {"audio": {"data": audio_b64, "format": "wav"}}}],
            "usage": {"completion_tokens": 4},
        }

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=mock_response)

        adapter = _make_adapter(mock_client)
        plan = RenderPlan(
            id="job_nostore",
            text="测试",
            processed_text="测试",
            profile_id="profile_test",
            provider="xiaomi_mimo",
            provider_voice_id="v1",
            model="mimo-v2.5-tts",
        )

        with patch("app.core.database.get_engine", return_value=tmp_engine), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_request_id", return_value=None), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_job_id", return_value="job_nostore"), \
             patch("app.utils.files.storage_path", return_value=tempfile.mktemp(suffix=".wav")):
            asyncio.get_event_loop().run_until_complete(adapter.render_sync(plan))

        with Session(tmp_engine) as session:
            logs = list(session.exec(select(ProviderCallLog)).all())

        assert logs, "Expected at least one log"
        log = logs[0]
        # Model has no request_payload / response_json / audio fields; confirm no large data
        # Check the fields that exist on the model
        assert not hasattr(log, "request_payload") or not log.request_payload
        assert not hasattr(log, "response_json") or not log.response_json
        assert not hasattr(log, "audio_data") or not log.audio_data


# ── Test 2: render_sync backfills usage_characters and provider_trace_id ─────

class TestCallLogUsageBackfill:
    def test_usage_and_trace_backfilled_after_render(self, tmp_engine):
        """After render_sync, the call log must have usage_characters and provider_trace_id."""
        from app.domain.render_plan import RenderPlan

        audio_b64 = _minimal_wav_base64()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "id": "mimo_trace_123",
            "choices": [{"message": {"audio": {"data": audio_b64, "format": "wav"}}}],
            "usage": {"completion_tokens": 12},
        }

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(return_value=mock_response)

        adapter = _make_adapter(mock_client)
        plan = RenderPlan(
            id="job_trace_test",
            text="你好",
            processed_text="你好",
            profile_id="profile_test",
            provider="xiaomi_mimo",
            provider_voice_id="v1",
            model="mimo-v2.5-tts",
        )

        with patch("app.core.database.get_engine", return_value=tmp_engine), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_request_id", return_value="req_001"), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_job_id", return_value="job_trace_test"), \
             patch("app.utils.files.storage_path", return_value=tempfile.mktemp(suffix=".wav")):
            asyncio.get_event_loop().run_until_complete(adapter.render_sync(plan))

        with Session(tmp_engine) as session:
            logs = list(session.exec(select(ProviderCallLog)).all())

        assert len(logs) == 1
        log = logs[0]
        assert log.usage_characters == 12, f"Expected 12, got {log.usage_characters}"
        assert log.provider_trace_id == "mimo_trace_123", \
            f"Expected mimo_trace_123, got {log.provider_trace_id}"


# ── Test 3: failure writes ProviderCallLog with error fields ─────────────────

class TestCallLogOnFailure:
    def test_timeout_writes_error_call_log(self, tmp_engine):
        """TimeoutException must write ProviderCallLog with error fields."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

        adapter = _make_adapter(mock_client)

        with patch("app.core.database.get_engine", return_value=tmp_engine), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_request_id", return_value=None), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_job_id", return_value=None):
            with pytest.raises(Exception):
                asyncio.get_event_loop().run_until_complete(
                    adapter._request("POST", "/v1/chat/completions", json={})
                )

        with Session(tmp_engine) as session:
            logs = list(session.exec(select(ProviderCallLog)).all())

        assert len(logs) == 1
        log = logs[0]
        assert log.provider == "xiaomi_mimo"
        assert log.status_code is None
        assert log.error_type == "TimeoutException"
        assert log.error_message is not None
        assert len(log.error_message) <= 500

    def test_network_error_writes_error_call_log(self, tmp_engine):
        """NetworkError must write ProviderCallLog with error_type=NetworkError."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.request = AsyncMock(side_effect=httpx.NetworkError("connection refused"))

        adapter = _make_adapter(mock_client)

        with patch("app.core.database.get_engine", return_value=tmp_engine), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_request_id", return_value=None), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_job_id", return_value=None):
            with pytest.raises(Exception):
                asyncio.get_event_loop().run_until_complete(
                    adapter._request("POST", "/v1/chat/completions", json={})
                )

        with Session(tmp_engine) as session:
            logs = list(session.exec(select(ProviderCallLog)).all())

        assert len(logs) == 1
        log = logs[0]
        assert log.error_type == "NetworkError"
        assert log.status_code is None

    def test_call_log_failure_does_not_raise(self, tmp_engine):
        """If _save_call_log itself fails, no extra exception must propagate from it."""
        from app.providers.xiaomi_mimo_chat_tts_adapter import XiaomiMiMoChatTTSAdapter
        from app.domain.provider_config import ProviderConfig

        mock_provider_config = MagicMock(spec=ProviderConfig)
        mock_provider_config.name = "xiaomi_mimo"
        mock_provider_config.resolved_api_key = "test_key"
        mock_provider_config.resolved_base_url = "https://fake.xiaomi.test"
        mock_provider_config.default_model = None
        mock_provider_config.endpoints = None

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_client.request = AsyncMock(return_value=mock_response)

        adapter = XiaomiMiMoChatTTSAdapter(
            provider_config=mock_provider_config,
            http_client=mock_client,
        )

        # Patch get_engine to raise — simulating DB unavailability
        with patch("app.core.database.get_engine", side_effect=RuntimeError("DB down")), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_request_id", return_value=None), \
             patch("app.providers.xiaomi_mimo_chat_tts_adapter.get_job_id", return_value=None):
            # _request must succeed despite call log failure
            result = asyncio.get_event_loop().run_until_complete(
                adapter._request("POST", "/v1/chat/completions", json={})
            )

        assert result.status_code == 200


# ── Test 4: StatsService shows AudioAsset-only providers ────────────────────

class TestStatsServiceAudioAssetOnlyProvider:
    def test_audio_asset_only_provider_appears_in_by_provider(self, tmp_engine):
        """Provider with AudioAsset but no ProviderCallLog must appear in by_provider."""
        with Session(tmp_engine) as session:
            job = VoiceJob(
                id="job_mimo_only",
                job_type="render",
                status="success",
                provider="xiaomi_mimo",
                created_at="2026-05-17T10:00:00",
                updated_at="2026-05-17T10:00:00",
            )
            asset = AudioAsset(
                id="asset_mimo_only",
                job_id="job_mimo_only",
                provider="xiaomi_mimo",
                file_path="/tmp/fake.wav",
                usage_characters=50,
                duration_ms=1000,
                created_at="2026-05-17T10:00:00",
            )
            session.add(job)
            session.add(asset)
            session.commit()

        svc = StatsService()
        with Session(tmp_engine) as session:
            result = svc.get_summary(session)

        assert "xiaomi_mimo" in result["by_provider"], \
            "xiaomi_mimo must appear in by_provider even without ProviderCallLog"
        row = result["by_provider"]["xiaomi_mimo"]
        assert row["api_calls"] == 0
        assert row["characters_used"] == 50

    def test_both_call_log_and_asset_no_double_count(self, tmp_engine):
        """When both ProviderCallLog and AudioAsset exist, characters_used is max, not sum."""
        with Session(tmp_engine) as session:
            job = VoiceJob(
                id="job_both",
                job_type="render",
                status="success",
                provider="xiaomi_mimo",
                created_at="2026-05-17T10:00:00",
                updated_at="2026-05-17T10:00:00",
            )
            log = ProviderCallLog(
                id="clog_both",
                provider="xiaomi_mimo",
                api_path="/v1/chat/completions",
                method="POST",
                status_code=200,
                duration_ms=500,
                usage_characters=40,
                created_at="2026-05-17T10:00:00",
            )
            asset = AudioAsset(
                id="asset_both",
                job_id="job_both",
                provider="xiaomi_mimo",
                file_path="/tmp/fake_both.wav",
                usage_characters=50,
                duration_ms=1000,
                created_at="2026-05-17T10:00:00",
            )
            session.add(job)
            session.add(log)
            session.add(asset)
            session.commit()

        svc = StatsService()
        with Session(tmp_engine) as session:
            result = svc.get_summary(session)

        row = result["by_provider"]["xiaomi_mimo"]
        # max(40, 50) == 50, not 40+50=90
        assert row["characters_used"] == 50, \
            f"Expected max(40,50)=50, got {row['characters_used']}"
        assert row["api_calls"] == 1
