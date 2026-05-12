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
