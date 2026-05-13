import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.time import utc_now_iso
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile
from app.models.provider_voice import ProviderVoice


@pytest.fixture
def custom_profile_with_binding(session: Session):
    """Create a custom profile with a minimax binding for testing."""
    now = utc_now_iso()
    profile = VoiceProfile(
        id="test_custom_profile",
        name="Test Profile",
        description="A profile for variant service testing.",
        gender_style="neutral",
        age_style="adult",
        tone_style="calm",
        emotion_style="neutral",
        speed_style="normal",
        pause_style="normal",
        scene_tags_json='["test"]',
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    binding = VoiceBinding(
        id="binding_minimax_test_custom_profile",
        profile_id=profile.id,
        provider="minimax",
        model="speech-2.8-hd",
        provider_voice_id="English_expressive_narrator",
        params_json='{"speed":0.9,"emotion":"neutral"}',
        priority=1,
        status="available",
        created_at=now,
        updated_at=now,
    )
    mock_binding = VoiceBinding(
        id="binding_mock_test_custom_profile",
        profile_id=profile.id,
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="mock_voice",
        params_json='{}',
        priority=1,
        status="available",
        created_at=now,
        updated_at=now,
    )
    session.add(profile)
    session.add(binding)
    session.add(mock_binding)

    for pv_spec in [
        {"id": "pv_minimax_test", "provider": "minimax", "provider_voice_id": "English_expressive_narrator"},
        {"id": "pv_mock_test", "provider": "mock", "provider_voice_id": "mock_voice"},
    ]:
        pv = ProviderVoice(
            id=pv_spec["id"],
            provider=pv_spec["provider"],
            provider_voice_id=pv_spec["provider_voice_id"],
            voice_type="voice_cloning",
            name=f"Mock PV {pv_spec['provider_voice_id']}",
            status="available",
            created_at=now,
            updated_at=now,
        )
        session.add(pv)
    session.commit()
    return profile, binding


def test_render_variants_default_profile(test_app, seed_profile, seed_mock_binding):
    """Default profile deep_night_programmer is used when profile_id not passed."""
    resp = TestClient(test_app).post(
        "/api/voice/variants/render",
        json={
            "text": "这是一段测试文本。",
            "variant_count": 3,
            "provider": "mock",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["group_id"]
    assert len(data["variants"]) == 3
    for v in data["variants"]:
        assert v["profile_id"] == "deep_night_programmer"
        assert v["job_id"]
        assert v["audio_asset_id"]


def test_render_variants_custom_profile(test_app, custom_profile_with_binding):
    """Custom profile is used when profile_id is passed."""
    resp = TestClient(test_app).post(
        "/api/voice/variants/render",
        json={
            "text": "自定义配置文本。",
            "profile_id": "test_custom_profile",
            "variant_count": 2,
            "provider": "mock",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["group_id"]
    assert len(data["variants"]) == 2
    for v in data["variants"]:
        assert v["profile_id"] == "test_custom_profile"


def test_render_variants_count(test_app, seed_profile, seed_mock_binding):
    """variant_count=1 returns 1 variant; variant_count=5 returns 5 variants."""
    for count, expected in [(1, 1), (5, 5)]:
        resp = TestClient(test_app).post(
            "/api/voice/variants/render",
            json={
                "text": "变体数量测试。",
                "variant_count": count,
                "provider": "mock",
            },
        )
        assert resp.status_code == 200
        assert len(resp.json()["variants"]) == expected


def test_render_variants_each_has_job_and_audio(test_app, seed_profile, seed_mock_binding):
    """Each variant has a non-null job_id and audio_asset_id under mock provider."""
    resp = TestClient(test_app).post(
        "/api/voice/variants/render",
        json={
            "text": "完整字段验证。",
            "variant_count": 3,
            "provider": "mock",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["variants"]) == 3
    for v in data["variants"]:
        assert v["job_id"], "job_id should not be empty"
        assert v["audio_asset_id"], "audio_asset_id should not be empty"
        assert v["speed"] is not None
        assert v["emotion"] is not None


class TestVoiceVariantResourceGuard:
    """Tests for Resource Guard integration in VoiceVariantService."""

    @pytest.fixture(autouse=True)
    def reset_guard(self):
        """Reset resource guard state before and after each test."""
        from app.services.resource_guard_service import reset_resource_guard_for_tests
        reset_resource_guard_for_tests()
        yield
        reset_resource_guard_for_tests()

    @pytest.mark.asyncio
    async def test_variants_rejected_when_slot_full(self, session, seed_profile, seed_mock_binding):
        """When voice_variants limit=1 is held, second request is rejected with 429 and creates no group."""
        from unittest.mock import patch
        from app.services.voice_variant_service import VoiceVariantService
        from app.services.resource_guard_service import ResourceLimitExceeded
        from app.domain.schemas import VoiceVariantRenderRequest
        from app.repositories import voice_variant_repo

        create_group_called = False
        render_voice_called = False

        original_create_group = voice_variant_repo.create_group

        def tracked_create_group(sess, group):
            nonlocal create_group_called
            create_group_called = True
            return original_create_group(sess, group)

        class CheckedRenderAdapter:
            provider_name = "minimax"

            async def render_sync(self, plan):
                nonlocal render_voice_called
                render_voice_called = True
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

        svc = VoiceVariantService()

        # First: hold the voice_variants slot
        from app.services.resource_guard_service import get_resource_guard
        guard = get_resource_guard()
        lease = await guard._acquire(provider="minimax", operation="voice_variants", job_id=None)

        # Second: try to call render_variants - should be rejected before any adapter is called
        with patch("app.services.voice_render_service.get_provider", return_value=CheckedRenderAdapter()):
            with patch("app.repositories.voice_variant_repo.create_group", side_effect=tracked_create_group):
                req = VoiceVariantRenderRequest(
                    text="测试文本",
                    profile_id="deep_night_programmer",
                    provider="minimax",
                    variant_count=3,
                    confirm_cost=True,
                )
                with pytest.raises(ResourceLimitExceeded) as exc_info:
                    await svc.render_variants(session, req)
                assert exc_info.value.status_code == 429
                assert exc_info.value.code == "RESOURCE_LIMIT_EXCEEDED"

        assert create_group_called is False, "create_group should not be called when voice_variants guard rejects"
        assert render_voice_called is False, "render_service.render_voice should not be called when voice_variants guard rejects"

        # Cleanup: release the held slot
        await guard._release(lease)

    @pytest.mark.asyncio
    async def test_variants_not_affected_by_t2a_sync_limit(self, session, seed_profile, seed_mock_binding):
        """When t2a_sync is full, voice_variants should still succeed because it uses resource_guard_already_acquired=True."""
        from unittest.mock import patch
        from app.services.voice_variant_service import VoiceVariantService
        from app.services.voice_render_service import VoiceRenderService
        from app.services.resource_guard_service import ResourceLimitExceeded, get_resource_guard
        from app.domain.schemas import VoiceVariantRenderRequest, VoiceRenderRequest, VoiceRenderResponse

        # Track render_voice calls and their resource_guard_already_acquired parameter
        render_voice_calls = []

        async def tracked_render_voice(sess, req, voice_overrides=None, resource_guard_already_acquired=False):
            render_voice_calls.append({
                "resource_guard_already_acquired": resource_guard_already_acquired,
                "voice_overrides": voice_overrides,
            })
            # Return a mock response
            from app.domain.schemas import AudioAssetResponse
            return VoiceRenderResponse(
                job_id="mock_job",
                status="success",
                audio_asset=AudioAssetResponse(id="mock_audio", url="/mock.wav", duration_ms=1000, format="wav"),
                provider="minimax",
                model="speech-2.8-hd",
            )

        svc = VoiceVariantService()

        # Hold all t2a_sync slots (limit=2)
        guard = get_resource_guard()
        lease1 = await guard._acquire(provider="minimax", operation="t2a_sync", job_id=None)
        lease2 = await guard._acquire(provider="minimax", operation="t2a_sync", job_id=None)

        # t2a_sync is now full, but voice_variants should not be affected
        with patch.object(VoiceRenderService, "render_voice", side_effect=tracked_render_voice):
            req = VoiceVariantRenderRequest(
                text="测试文本",
                profile_id="deep_night_programmer",
                provider="minimax",
                variant_count=2,
                confirm_cost=True,
            )
            # Should NOT raise ResourceLimitExceeded for t2a_sync
            result = await svc.render_variants(session, req)

        # Verify render_voice was called with resource_guard_already_acquired=True
        assert len(render_voice_calls) == 2, f"Expected 2 render_voice calls, got {len(render_voice_calls)}"
        for call in render_voice_calls:
            assert call["resource_guard_already_acquired"] is True, "render_voice should be called with resource_guard_already_acquired=True"

        # Verify result
        assert result.group_id is not None
        assert len(result.variants) == 2

        # Cleanup
        await guard._release(lease1)
        await guard._release(lease2)

    @pytest.mark.asyncio
    async def test_variants_success_path_works(self, session, seed_profile, seed_mock_binding):
        """Normal variants rendering should work correctly with mocked render_voice."""
        from unittest.mock import patch
        from app.services.voice_variant_service import VoiceVariantService
        from app.services.voice_render_service import VoiceRenderService
        from app.domain.schemas import VoiceVariantRenderRequest, VoiceRenderRequest, VoiceRenderResponse, AudioAssetResponse

        async def mock_render_voice(sess, req, voice_overrides=None, resource_guard_already_acquired=False):
            return VoiceRenderResponse(
                job_id="variant_job",
                status="success",
                audio_asset=AudioAssetResponse(id="variant_audio", url="/variant.wav", duration_ms=2000, format="wav"),
                provider="minimax",
                model="speech-2.8-hd",
            )

        svc = VoiceVariantService()

        with patch.object(VoiceRenderService, "render_voice", side_effect=mock_render_voice):
            req = VoiceVariantRenderRequest(
                text="测试文本",
                profile_id="deep_night_programmer",
                provider="minimax",
                variant_count=3,
                confirm_cost=True,
            )
            result = await svc.render_variants(session, req)

        assert result.group_id is not None
        assert len(result.variants) == 3
        for v in result.variants:
            assert v.job_id == "variant_job"
            assert v.audio_asset_id == "variant_audio"
