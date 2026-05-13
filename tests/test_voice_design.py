import asyncio

import pytest
from fastapi.testclient import TestClient


def test_design_voice(test_app):
    """POST /api/voice/design/create with mock returns voice_id."""
    resp = TestClient(test_app).post(
        "/api/voice/design/create",
        json={"prompt": "成熟女性，温柔知性", "preview_text": "今天天气真好"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "voice_id" in data
    assert data["message"] == "设计成功"


def test_design_voice_custom_id(test_app):
    """自定义voice_id被正确返回。"""
    resp = TestClient(test_app).post(
        "/api/voice/design/create",
        json={"prompt": "低沉男声", "preview_text": "测试文本", "voice_id": "my_custom_voice"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    assert resp.json()["voice_id"] == "my_custom_voice"


def test_design_empty_prompt(test_app):
    """空prompt返回422。"""
    resp = TestClient(test_app).post(
        "/api/voice/design/create",
        json={"prompt": "", "preview_text": "测试"},
        params={"provider": "mock"},
    )
    assert resp.status_code == 422


def test_design_preview_text_too_long(test_app):
    """preview_text超500字返回422。"""
    resp = TestClient(test_app).post(
        "/api/voice/design/create",
        json={"prompt": "测试", "preview_text": "a" * 501},
        params={"provider": "mock"},
    )
    assert resp.status_code == 422


def test_voice_design_provider_signature_has_no_model():
    """design_voice() adapter method has no 'model' parameter (official API does not support it)."""
    import inspect
    from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter

    sig = inspect.signature(MiniMaxSpeechAdapter.design_voice)
    assert "model" not in sig.parameters, \
        f"design_voice should not have 'model' parameter, but has: {list(sig.parameters.keys())}"


class TestDesignServiceUpsert:
    def test_design_success_upserts_provider_voice(self, test_app, session):
        """design_voice success writes a record to provider_voices."""
        from unittest.mock import patch
        from app.repositories.provider_voice_repo import get_provider_voice

        class FakeAdapter:
            provider_name = "mock"
            async def design_voice(self, prompt, preview_text, voice_id=None):
                return {
                    "voice_id": voice_id or "test_design_voice_01",
                    "trial_audio_hex": None,
                    "message": "ok",
                }

        with patch("app.services.voice_design_service.get_provider", return_value=FakeAdapter()):
            from app.services.voice_design_service import VoiceDesignService
            svc = VoiceDesignService()
            from app.domain.schemas import VoiceDesignRequest
            req = VoiceDesignRequest(
                prompt="成熟女性，温柔知性",
                preview_text="这是一段试听文本。",
            )
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                svc.design_voice(session, "mock", req)
            )

        pv = get_provider_voice(session, provider="mock", provider_voice_id="test_design_voice_01")
        assert pv is not None, "provider_voice should be upserted after design success"
        assert pv.voice_type == "voice_generation"
        assert pv.status == "available"

    def test_design_empty_voice_id_raises_error(self, test_app, session):
        """adapter returns empty voice_id → ProviderError, not a false success."""
        from unittest.mock import patch
        from app.core.errors import ProviderError

        class EmptyVoiceIdAdapter:
            provider_name = "mock"
            async def design_voice(self, prompt, preview_text, voice_id=None):
                return {
                    "voice_id": None,
                    "trial_audio_hex": None,
                }

        with patch("app.services.voice_design_service.get_provider", return_value=EmptyVoiceIdAdapter()):
            from app.services.voice_design_service import VoiceDesignService
            svc = VoiceDesignService()
            from app.domain.schemas import VoiceDesignRequest
            req = VoiceDesignRequest(
                prompt="测试",
                preview_text="这是一段试听文本。",
            )
            with pytest.raises(ProviderError) as exc:
                import asyncio
                asyncio.get_event_loop().run_until_complete(
                    svc.design_voice(session, "mock", req)
                )
        assert "empty voice_id" in str(exc.value.message).lower()


class TestVoiceDesignResourceGuard:
    """Tests for Resource Guard integration in VoiceDesignService."""

    @pytest.fixture(autouse=True)
    def reset_guard(self):
        """Reset resource guard state before and after each test."""
        from app.services.resource_guard_service import reset_resource_guard_for_tests
        reset_resource_guard_for_tests()
        yield
        reset_resource_guard_for_tests()

    @pytest.mark.asyncio
    async def test_voice_design_rejected_when_slot_full(self, session):
        """When voice_design limit=1 is held, second request is rejected with 429."""
        from unittest.mock import patch, AsyncMock
        from app.services.voice_design_service import VoiceDesignService
        from app.services.resource_guard_service import ResourceLimitExceeded

        adapter_called = False

        class CheckedDesignAdapter:
            provider_name = "minimax"
            async def design_voice(self, prompt, preview_text, voice_id=None):
                nonlocal adapter_called
                adapter_called = True
                return {"voice_id": "test", "trial_audio_hex": None}

        svc = VoiceDesignService()

        # First: hold the voice_design slot
        from app.services.resource_guard_service import get_resource_guard
        guard = get_resource_guard()
        lease = await guard._acquire(provider="minimax", operation="voice_design", job_id=None)

        # Second: try to call design_voice - should be rejected before adapter is called
        with patch("app.services.voice_design_service.get_provider", return_value=CheckedDesignAdapter()):
            from app.domain.schemas import VoiceDesignRequest
            req = VoiceDesignRequest(
                prompt="测试",
                preview_text="这是一段试听文本。",
                confirm_cost=True,
            )
            with pytest.raises(ResourceLimitExceeded) as exc_info:
                await svc.design_voice(session, "minimax", req)
            assert exc_info.value.status_code == 429
            assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"

        assert adapter_called is False, "adapter.design_voice should not be called when Resource Guard rejects"

        # Cleanup: release the held slot
        await guard._release(lease)