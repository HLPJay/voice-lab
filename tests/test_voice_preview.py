from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.domain.schemas import ProviderVoicePreviewRequest


class TestProviderVoicePreviewSchema:
    def test_empty_provider_voice_id_rejected(self):
        with pytest.raises(ValueError) as exc_info:
            ProviderVoicePreviewRequest(provider_voice_id="")
        assert "provider_voice_id" in str(exc_info.value)

    def test_empty_text_rejected(self):
        with pytest.raises(ValueError) as exc_info:
            ProviderVoicePreviewRequest(text="", provider_voice_id="valid_id")
        assert "text" in str(exc_info.value)

    def test_output_format_mp3_rejected(self):
        with pytest.raises(ValueError) as exc_info:
            ProviderVoicePreviewRequest(
                provider_voice_id="test",
                text="hello",
                output_format="mp3",
            )
        assert "output_format" in str(exc_info.value)

    def test_valid_request_passes(self):
        req = ProviderVoicePreviewRequest(
            provider_voice_id="voice_123",
            text="你好，这是一段试听文本。",
            provider="mock",
            model="speech-2.8-hd",
            audio_format="mp3",
            output_format="hex",
        )
        assert req.provider_voice_id == "voice_123"
        assert req.text == "你好，这是一段试听文本。"
        assert req.output_format == "hex"


class TestProviderVoicePreviewAPI:
    def test_preview_returns_200_with_audio_asset(self, test_app):
        resp = TestClient(test_app).post(
            "/api/voice/provider-voices/preview",
            json={
                "provider": "mock",
                "provider_voice_id": "mock_voice_system",
                "model": "speech-2.8-hd",
                "text": "你好，这是一段试听测试。",
                "audio_format": "mp3",
                "output_format": "hex",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "mock"
        assert data["model"] == "speech-2.8-hd"
        assert data["provider_voice_id"] == "mock_voice_system"
        assert "audio_asset" in data
        assert data["audio_asset"]["id"]
        assert data["audio_asset"]["url"]

    def test_preview_with_speed_vol_pitch(self, test_app):
        resp = TestClient(test_app).post(
            "/api/voice/provider-voices/preview",
            json={
                "provider": "mock",
                "provider_voice_id": "mock_voice_system",
                "model": "speech-2.8-hd",
                "text": "参数试听测试。",
                "audio_format": "mp3",
                "output_format": "hex",
                "speed": 1.2,
                "vol": 1.5,
                "pitch": 2,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["audio_asset"]["id"]

    def test_preview_missing_text_returns_422(self, test_app):
        resp = TestClient(test_app).post(
            "/api/voice/provider-voices/preview",
            json={
                "provider": "mock",
                "provider_voice_id": "mock_voice_system",
                "model": "speech-2.8-hd",
                "audio_format": "mp3",
                "output_format": "hex",
            },
        )
        assert resp.status_code == 422

    def test_preview_missing_voice_id_returns_422(self, test_app):
        resp = TestClient(test_app).post(
            "/api/voice/provider-voices/preview",
            json={
                "provider": "mock",
                "model": "speech-2.8-hd",
                "text": "测试文本",
                "audio_format": "mp3",
                "output_format": "hex",
            },
        )
        assert resp.status_code == 422


class TestProviderVoicePreviewService:
    def test_plan_uses_preview_profile_id(self, test_app):
        """Verify RenderPlan is created with __preview__ profile_id."""
        from unittest.mock import patch, MagicMock
        from app.domain.render_plan import RenderPlan

        captured_plan = None

        class FakeAdapter:
            provider_name = "mock"

            async def list_voices(self, voice_type="all"):
                return []

            async def render_sync(self, plan: RenderPlan):
                nonlocal captured_plan
                captured_plan = plan
                from app.utils.audio import write_silent_wav
                from app.utils.files import storage_path
                from app.utils.id_generator import new_id
                from app.utils.audio import estimate_duration_ms
                audio_id = new_id("audio_file")
                audio_path = storage_path("audio", f"{audio_id}.wav")
                duration_ms = estimate_duration_ms(plan.processed_text)
                write_silent_wav(audio_path, duration_ms=min(duration_ms, 2000), sample_rate=16000)
                from app.providers.base import ProviderRenderResult
                return ProviderRenderResult(
                    audio_path=str(audio_path),
                    duration_ms=duration_ms,
                    usage_characters=len(plan.text),
                    trace_id="mock_trace",
                    response_json={"mock": True},
                    timeline=[],
                    metadata={"mock": True},
                )

        with patch("app.services.voice_preview_service.get_provider", return_value=FakeAdapter()):
            resp = TestClient(test_app).post(
                "/api/voice/provider-voices/preview",
                json={
                    "provider": "mock",
                    "provider_voice_id": "mock_voice_system",
                    "model": "speech-2.8-hd",
                    "text": "direct preview test",
                    "audio_format": "mp3",
                    "output_format": "hex",
                },
            )
        assert resp.status_code == 200
        assert captured_plan is not None
        assert captured_plan.profile_id == "__preview__"
        assert captured_plan.provider_voice_id == "mock_voice_system"
