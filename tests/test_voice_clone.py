import asyncio

import pytest
from fastapi.testclient import TestClient


def test_upload_clone_audio(test_app):
    """POST /api/voice/clone/upload with mock file returns file_id."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/upload",
        files={"file": ("test.mp3", b"fake_audio_data")},
        data={"purpose": "voice_clone", "provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["file_id"] == 99999
    assert data["filename"] == "test.mp3"
    assert data["purpose"] == "voice_clone"


def test_upload_prompt_audio(test_app):
    """POST /api/voice/clone/upload with purpose=prompt_audio succeeds."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/upload",
        files={"file": ("prompt.wav", b"prompt_data")},
        data={"purpose": "prompt_audio", "provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["purpose"] == "prompt_audio"
    assert data["bytes"] == len(b"prompt_data")


def test_clone_voice(test_app):
    """POST /api/voice/clone/create returns voice_id."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/create",
        json={"voice_id": "test_clone_voice_01", "file_id": 99999},
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["voice_id"] == "test_clone_voice_01"
    assert "message" in data


def test_clone_voice_with_prompt(test_app):
    """Clone with prompt_file_id and prompt_text succeeds."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/create",
        json={
            "voice_id": "test_clone_with_prompt",
            "file_id": 99999,
            "prompt_file_id": 88888,
            "prompt_text": "这是一段参考文本。",
            "preview_text": "试听文本。",
            "model": "speech-2.8-hd",
        },
        params={"provider": "mock"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["voice_id"] == "test_clone_with_prompt"


def test_upload_invalid_purpose(test_app):
    """purpose不是voice_clone/prompt_audio时返回错误。"""
    resp = TestClient(test_app).post(
        "/api/voice/clone/upload",
        files={"file": ("test.mp3", b"data")},
        data={"purpose": "invalid_purpose", "provider": "mock"},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert "Invalid purpose" in data["error"]["message"]


def test_clone_invalid_voice_id(test_app):
    """voice_id不符合正则时返回422。"""
    resp = TestClient(test_app).post(
        "/api/voice/clone/create",
        json={"voice_id": "123invalid", "file_id": 99999},
        params={"provider": "mock"},
    )
    assert resp.status_code == 422


def test_clone_sensitive_bool_true_rejected(test_app, seed_mock_binding):
    """MiniMax API response with input_sensitive=True raises ProviderError."""
    from unittest.mock import patch
    from app.core.errors import ProviderError

    class SensitiveAdapter:
        async def clone_voice(self, request: dict) -> dict:
            # Simulate MiniMax response where content safety check fails
            raise ProviderError(
                "内容安全检测未通过",
                "input_sensitive=True, input_sensitive_type=1",
            )

    with patch("app.services.voice_clone_service.get_provider", return_value=SensitiveAdapter()):
        resp = TestClient(test_app).post(
            "/api/voice/clone/create",
            json={"voice_id": "test_sensitive_01", "file_id": 99999},
            params={"provider": "mock"},
        )
    assert resp.status_code == 400
    data = resp.json()
    assert "内容安全" in data["error"]["message"] or \
           "sensitive" in data["error"]["message"].lower()


def test_clone_prompt_pair_required(test_app):
    """Only prompt_file_id without prompt_text → 422 ValidationError."""
    resp = TestClient(test_app).post(
        "/api/voice/clone/create",
        json={
            "voice_id": "test_prompt_pair_01",
            "file_id": 99999,
            "prompt_file_id": 88888,
            # intentionally omit prompt_text
        },
        params={"provider": "mock"},
    )
    assert resp.status_code == 422


class TestMiniMaxCloneAdapter:
    def test_clone_success_uses_request_voice_id(self):
        """clone_voice returns request['voice_id'] even if body has no voice_id."""
        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
        from unittest.mock import patch

        adapter = MiniMaxSpeechAdapter()

        class MockResp:
            status_code = 200
            def raise_for_status(self): pass
            def json(self):
                # MiniMax success response without voice_id in body
                return {"base_resp": {"status_code": 0}, "demo_audio": None}

        async def mock_request(method, path, **kwargs):
            return MockResp()

        with patch.object(adapter, "_request", mock_request):
            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                adapter.clone_voice({
                    "voice_id": "my_custom_voice_id",
                    "file_id": 12345,
                })
            )

        assert result["voice_id"] == "my_custom_voice_id"

    def test_clone_duplicate_error_raises_provider_error(self):
        """MiniMax returns status_code=2039 duplicate → ProviderError with duplicate detail."""
        from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
        from app.core.errors import ProviderError
        from unittest.mock import patch

        adapter = MiniMaxSpeechAdapter()

        class MockResp:
            status_code = 200
            def raise_for_status(self): pass
            def json(self):
                return {
                    "base_resp": {
                        "status_code": 2039,
                        "status_msg": "voice clone voice id duplicate"
                    }
                }

        async def mock_request(method, path, **kwargs):
            return MockResp()

        with patch.object(adapter, "_request", mock_request):
            with pytest.raises(ProviderError) as exc_info:
                import asyncio
                asyncio.get_event_loop().run_until_complete(
                    adapter.clone_voice({
                        "voice_id": "duplicate_voice",
                        "file_id": 12345,
                    })
                )
        assert "duplicate" in str(exc_info.value.detail).lower()


class TestCloneServiceUpsert:
    def test_clone_success_upserts_provider_voice(self, test_app, session):
        """clone_voice success writes a record to provider_voices."""
        from unittest.mock import patch, AsyncMock
        from app.models.provider_voice import ProviderVoice
        from app.repositories.provider_voice_repo import get_provider_voice

        class FakeAdapter:
            provider_name = "mock"
            async def clone_voice(self, request):
                return {
                    "voice_id": request["voice_id"],
                    "demo_audio_url": None,
                    "duration_ms": 5000,
                    "usage_characters": 50,
                }

        with patch("app.services.voice_clone_service.get_provider", return_value=FakeAdapter()):
            from app.services.voice_clone_service import VoiceCloneService
            svc = VoiceCloneService()
            from app.domain.schemas import VoiceCloneRequest
            req = VoiceCloneRequest(
                voice_id="clone_test_voice_01",
                file_id=12345,
            )
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                svc.clone_voice(session, "mock", req)
            )

        pv = get_provider_voice(session, provider="mock", provider_voice_id="clone_test_voice_01")
        assert pv is not None, "provider_voice should be upserted after clone success"
        assert pv.voice_type == "voice_cloning"
        assert pv.status == "available"

    def test_clone_empty_voice_id_raises_error(self, test_app, session):
        """adapter returns empty voice_id → ProviderError, not a false success."""
        from unittest.mock import patch
        from app.core.errors import ProviderError

        class EmptyVoiceIdAdapter:
            provider_name = "mock"
            async def clone_voice(self, request):
                return {
                    "voice_id": None,
                    "demo_audio_url": None,
                }

        with patch("app.services.voice_clone_service.get_provider", return_value=EmptyVoiceIdAdapter()):
            from app.services.voice_clone_service import VoiceCloneService
            svc = VoiceCloneService()
            from app.domain.schemas import VoiceCloneRequest
            req = VoiceCloneRequest(voice_id="some_id_voice", file_id=12345)
            with pytest.raises(ProviderError) as exc:
                import asyncio
                asyncio.get_event_loop().run_until_complete(
                    svc.clone_voice(session, "mock", req)
                )
        assert "empty voice_id" in str(exc.value.message).lower()


class TestVoiceCloneResourceGuard:
    """Tests for Resource Guard integration in VoiceCloneService."""

    @pytest.fixture(autouse=True)
    def reset_guard(self):
        """Reset resource guard state before and after each test."""
        from app.services.resource_guard_service import reset_resource_guard_for_tests
        reset_resource_guard_for_tests()
        yield
        reset_resource_guard_for_tests()

    @pytest.mark.asyncio
    async def test_upload_rejected_when_slot_full(self, session):
        """When voice_clone_upload limit=1 is held, second request is rejected with 429."""
        from unittest.mock import patch
        from app.services.voice_clone_service import VoiceCloneService
        from app.services.resource_guard_service import ResourceLimitExceeded

        adapter_called = False

        class CheckedUploadAdapter:
            provider_name = "minimax"
            async def upload_voice_file(self, file_data, filename, purpose):
                nonlocal adapter_called
                adapter_called = True
                return {"file_id": "test_file", "filename": filename, "purpose": purpose}

        svc = VoiceCloneService()

        # First: hold the voice_clone_upload slot
        from app.services.resource_guard_service import get_resource_guard
        guard = get_resource_guard()
        lease = await guard._acquire(provider="minimax", operation="voice_clone_upload", job_id=None)

        # Second: try to call upload_audio - should be rejected before adapter is called
        with patch("app.services.voice_clone_service.get_provider", return_value=CheckedUploadAdapter()):
            with pytest.raises(ResourceLimitExceeded) as exc_info:
                await svc.upload_audio("minimax", b"fake_audio_data", "test.mp3", "voice_clone")
            assert exc_info.value.status_code == 429
            assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"

        assert adapter_called is False, "adapter.upload_voice_file should not be called when Resource Guard rejects"

        # Cleanup: release the held slot
        await guard._release(lease)

    @pytest.mark.asyncio
    async def test_clone_rejected_when_slot_full(self, session):
        """When voice_clone_create limit=1 is held, second request is rejected with 429."""
        from unittest.mock import patch
        from app.services.voice_clone_service import VoiceCloneService
        from app.services.resource_guard_service import ResourceLimitExceeded

        adapter_called = False

        class CheckedCloneAdapter:
            provider_name = "minimax"
            async def clone_voice(self, request):
                nonlocal adapter_called
                adapter_called = True
                return {"voice_id": "test_clone", "demo_audio_url": None}

        svc = VoiceCloneService()

        # First: hold the voice_clone_create slot
        from app.services.resource_guard_service import get_resource_guard
        guard = get_resource_guard()
        lease = await guard._acquire(provider="minimax", operation="voice_clone_create", job_id=None)

        # Second: try to call clone_voice - should be rejected before adapter is called
        with patch("app.services.voice_clone_service.get_provider", return_value=CheckedCloneAdapter()):
            from app.domain.schemas import VoiceCloneRequest
            req = VoiceCloneRequest(
                voice_id="test_clone_01",
                file_id=12345,
                confirm_cost=True,
            )
            with pytest.raises(ResourceLimitExceeded) as exc_info:
                await svc.clone_voice(session, "minimax", req)
            assert exc_info.value.status_code == 429
            assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"

        assert adapter_called is False, "adapter.clone_voice should not be called when Resource Guard rejects"

        # Cleanup: release the held slot
        await guard._release(lease)