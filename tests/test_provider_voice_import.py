import json

import pytest
from unittest.mock import patch, AsyncMock

from app.core.errors import ProviderError, ValidationError
from app.domain.schemas import AudioAssetResponse, ProviderVoiceImportRequest
from app.repositories.provider_voice_repo import get_provider_voice
from app.services.provider_voice_import_service import ProviderVoiceImportService


class TestProviderVoiceImportService:
    def test_verify_false_direct_upsert(self, session):
        """verify=False → 直接 upsert provider_voice，metadata.verified=False。"""
        import asyncio

        svc = ProviderVoiceImportService()
        req = ProviderVoiceImportRequest(
            provider="mock",
            provider_voice_id="import_no_verify_01",
            voice_type="voice_generation",
            verify=False,
            model="speech-2.8-hd",
            preview_text="不需要试听。",
        )
        result = asyncio.get_event_loop().run_until_complete(
            svc.import_voice(session, req)
        )

        assert result.verified is False
        assert result.audio_asset is None

        pv = get_provider_voice(session, provider="mock", provider_voice_id="import_no_verify_01")
        assert pv is not None
        assert pv.status == "available"
        assert pv.voice_type == "voice_generation"
        metadata = json.loads(pv.metadata_json)
        assert metadata["source"] == "manual_import"
        assert metadata["verified"] is False

    def test_verify_true_preview_success_upserts_provider_voice(self, session):
        """verify=True 且 preview 成功 → upsert provider_voice，status=available。"""
        import asyncio
        from app.domain.schemas import ProviderVoicePreviewResponse

        class FakePreviewResult:
            audio_asset = AudioAssetResponse(
                id="audio_test_001",
                url="/api/voice/assets/audio_test_001/download",
                duration_ms=1000,
                format="mp3",
            )

        svc = ProviderVoiceImportService()

        async def fake_preview(*args, **kwargs):
            return FakePreviewResult()

        with patch.object(svc.preview_service, "preview", new_callable=AsyncMock) as mock_preview:
            mock_preview.side_effect = fake_preview
            req = ProviderVoiceImportRequest(
                provider="mock",
                provider_voice_id="import_test_voice_01",
                voice_type="voice_cloning",
                verify=True,
                model="speech-2.8-hd",
                preview_text="你好，这是导入试听。",
            )
            result = asyncio.get_event_loop().run_until_complete(
                svc.import_voice(session, req)
            )

        assert result.provider == "mock"
        assert result.provider_voice_id == "import_test_voice_01"
        assert result.voice_type == "voice_cloning"
        assert result.status == "available"
        assert result.verified is True
        assert result.audio_asset is not None

        pv = get_provider_voice(session, provider="mock", provider_voice_id="import_test_voice_01")
        assert pv is not None
        assert pv.status == "available"
        assert pv.voice_type == "voice_cloning"

    def test_verify_true_preview_failure_raises_no_upsert(self, session):
        """verify=True 且 preview 失败 → 不写入 available，返回错误。"""
        import asyncio

        svc = ProviderVoiceImportService()

        with patch.object(svc.preview_service, "preview", new_callable=AsyncMock) as mock_preview:
            mock_preview.side_effect = ProviderError("MiniMax T2A failed", "audio length too short")
            req = ProviderVoiceImportRequest(
                provider="mock",
                provider_voice_id="nonexistent_voice_01",
                voice_type="voice_cloning",
                verify=True,
                model="speech-2.8-hd",
                preview_text="测试。",
            )
            with pytest.raises(ProviderError) as exc_info:
                asyncio.get_event_loop().run_until_complete(
                    svc.import_voice(session, req)
                )
            assert "导入失败" in str(exc_info.value.message)

        pv = get_provider_voice(session, provider="mock", provider_voice_id="nonexistent_voice_01")
        assert pv is None, "不应写入 provider_voice when preview fails"

    def test_invalid_voice_type_rejected_at_schema_level(self, session):
        """voice_type 不是 voice_cloning/voice_generation 时 Pydantic 在构造时就拒绝。"""
        from pydantic_core import ValidationError as PydanticValidationError

        with pytest.raises((ValidationError, PydanticValidationError)):
            ProviderVoiceImportRequest(
                provider="mock",
                provider_voice_id="any_voice",
                voice_type="system",  # invalid
                verify=False,
            )

    def test_import_then_bind_succeeds(self, session):
        """导入成功后可以创建 binding。"""
        import asyncio
        from app.core.time import utc_now_iso
        from app.domain.schemas import VoiceBindingCreate
        from app.models.voice_profile import VoiceProfile
        from app.services.voice_binding_service import VoiceBindingService

        now = utc_now_iso()
        profile = VoiceProfile(
            id="import_bind_profile",
            name="Import Test Profile",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        session.add(profile)
        session.commit()

        svc = ProviderVoiceImportService()
        asyncio.get_event_loop().run_until_complete(
            svc.import_voice(session, ProviderVoiceImportRequest(
                provider="mock",
                provider_voice_id="import_for_bind_01",
                voice_type="voice_cloning",
                verify=False,
            ))
        )

        binding_service = VoiceBindingService()
        binding_req = VoiceBindingCreate(
            provider="mock",
            model="speech-2.8-hd",
            provider_voice_id="import_for_bind_01",
            params={},
            priority=1,
        )
        binding = binding_service.create_profile_binding(session, "import_bind_profile", binding_req)
        assert binding.provider_voice_id == "import_for_bind_01"
        assert binding.profile_id == "import_bind_profile"
