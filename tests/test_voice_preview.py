import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

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
        assert "job_id" in data
        assert "status" in data
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
                "model": "speech-2.8-hd",
                "text": "测试文本",
                "audio_format": "mp3",
                "output_format": "hex",
            },
        )
        assert resp.status_code == 422


class TestProviderVoicePreviewService:
    def test_plan_uses_provider_voice_id_not_binding(self, test_app):
        """Verify RenderPlan uses the exact provider_voice_id passed in request, not from binding."""
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

        with patch("app.services.provider_voice_preview_service.get_provider", return_value=FakeAdapter()):
            resp = TestClient(test_app).post(
                "/api/voice/provider-voices/preview",
                json={
                    "provider_voice_id": "voice_a",
                    "model": "speech-2.8-hd",
                    "text": "direct preview test",
                    "audio_format": "mp3",
                    "output_format": "hex",
                    "confirm_cost": True,
                },
            )
        assert resp.status_code == 200
        assert captured_plan is not None
        # Must use the exact provider_voice_id from request, not from any binding
        assert captured_plan.provider_voice_id == "voice_a"
        # profile_id should NOT be a real profile
        assert captured_plan.profile_id == "provider_voice_preview"


class TestMiniMaxClonePayload:
    def test_clone_payload_excludes_input_sensitive(self):
        """MiniMaxSpeechAdapter.clone_voice() must NOT forward input_sensitive in the request payload."""
        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

        adapter = MiniMaxSpeechAdapter()
        captured_payload = None

        async def mock_request(method, path, **kwargs):
            nonlocal captured_payload
            captured_payload = kwargs.get("json", {})
            # Return a successful response
            class MockResp:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return {"base_resp": {"status_code": 0}, "voice_id": "test_voice"}
            return MockResp()

        with patch.object(adapter, "_request", mock_request):
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                adapter.clone_voice({
                    "voice_id": "test_voice",
                    "file_id": 12345,
                    "input_sensitive": True,  # This must NOT appear in payload
                    "model": "speech-2.8-hd",
                    "need_noise_reduction": True,
                })
            )

        assert captured_payload is not None
        assert "input_sensitive" not in captured_payload, \
            "input_sensitive must NOT be forwarded to MiniMax API"


class TestMiniMaxDesignVoice:
    def test_design_voice_base_resp_failure_raises_provider_error(self):
        """design_voice raises ProviderError when base_resp.status_code != 0."""
        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
        from app.core.errors import ProviderError

        adapter = MiniMaxSpeechAdapter()

        async def mock_request(method, path, **kwargs):
            class MockResp:
                status_code = 200
                def raise_for_status(self): pass
                def json(self):
                    return {
                        "base_resp": {
                            "status_code": 1008,
                            "status_msg": "insufficient balance"
                        }
                    }
            return MockResp()

        with patch.object(adapter, "_request", mock_request):
            with pytest.raises(ProviderError) as exc_info:
                import asyncio
                asyncio.get_event_loop().run_until_complete(
                    adapter.design_voice(
                        prompt="a warm male voice",
                        preview_text="hello world",
                        voice_id=None,
                    )
                )
        assert "insufficient balance" in str(exc_info.value.detail)


class TestProviderVoicePreviewResourceGuard:
    """Tests for Resource Guard integration in ProviderVoicePreviewService."""

    @pytest.fixture(autouse=True)
    def reset_guard(self):
        """Reset resource guard state before and after each test."""
        from app.services.resource_guard_service import reset_resource_guard_for_tests
        reset_resource_guard_for_tests()
        yield
        reset_resource_guard_for_tests()

    @pytest.mark.asyncio
    async def test_preview_rejected_when_slot_full(self, session):
        """When voice_preview limit=2 is full (2 held), third request is rejected with 429."""
        from unittest.mock import patch
        from app.services.provider_voice_preview_service import ProviderVoicePreviewService
        from app.services.resource_guard_service import ResourceLimitExceeded
        from app.domain.schemas import ProviderVoicePreviewRequest

        adapter_called = False

        class CheckedPreviewAdapter:
            provider_name = "minimax"

            async def render_sync(self, plan):
                nonlocal adapter_called
                adapter_called = True
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

        svc = ProviderVoicePreviewService()

        # First: hold both voice_preview slots (limit=2)
        from app.services.resource_guard_service import get_resource_guard
        guard = get_resource_guard()
        lease1 = await guard._acquire(provider="minimax", operation="voice_preview", job_id=None)
        lease2 = await guard._acquire(provider="minimax", operation="voice_preview", job_id=None)

        # Second: try to call preview - should be rejected before adapter is called
        with patch("app.services.provider_voice_preview_service.get_provider", return_value=CheckedPreviewAdapter()):
            req = ProviderVoicePreviewRequest(
                provider_voice_id="test_voice",
                model="speech-2.8-hd",
                text="测试文本",
                audio_format="mp3",
                output_format="hex",
                confirm_cost=True,
            )
            with pytest.raises(ResourceLimitExceeded) as exc_info:
                await svc.preview(session, "minimax", req)
            assert exc_info.value.status_code == 429
            assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"

        assert adapter_called is False, "adapter.render_sync should not be called when Resource Guard rejects"

        # Cleanup: release the held slots
        await guard._release(lease1)
        await guard._release(lease2)


class TestVoicePreviewResourceGuard:
    """Tests for Resource Guard integration in VoicePreviewService."""

    @pytest.fixture(autouse=True)
    def reset_guard(self):
        """Reset resource guard state before and after each test."""
        from app.services.resource_guard_service import reset_resource_guard_for_tests
        reset_resource_guard_for_tests()
        yield
        reset_resource_guard_for_tests()

    @pytest.mark.asyncio
    async def test_preview_rejected_when_slot_full(self, session):
        """When binding_voice_preview limit=2 is full (2 held), third request is rejected with 429."""
        from unittest.mock import patch
        from app.services.voice_preview_service import VoicePreviewService
        from app.services.resource_guard_service import ResourceLimitExceeded
        from app.domain.schemas import ProviderVoicePreviewRequest

        adapter_called = False

        class CheckedPreviewAdapter:
            provider_name = "minimax"

            async def render_sync(self, plan):
                nonlocal adapter_called
                adapter_called = True
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

        svc = VoicePreviewService()

        # First: hold both binding_voice_preview slots (limit=2)
        from app.services.resource_guard_service import get_resource_guard
        guard = get_resource_guard()
        lease1 = await guard._acquire(provider="minimax", operation="binding_voice_preview", job_id=None)
        lease2 = await guard._acquire(provider="minimax", operation="binding_voice_preview", job_id=None)

        # Second: try to call preview - should be rejected before adapter is called
        with patch("app.services.voice_preview_service.get_provider", return_value=CheckedPreviewAdapter()):
            req = ProviderVoicePreviewRequest(
                provider_voice_id="test_voice",
                model="speech-2.8-hd",
                text="测试文本",
                audio_format="mp3",
                output_format="hex",
                confirm_cost=True,
            )
            with pytest.raises(ResourceLimitExceeded) as exc_info:
                await svc.preview(session, req)
            assert exc_info.value.status_code == 429
            assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"

        assert adapter_called is False, "adapter.render_sync should not be called when Resource Guard rejects"

        # Cleanup: release the held slots
        await guard._release(lease1)
        await guard._release(lease2)
