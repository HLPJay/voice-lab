from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.config.product_config_models import ProductVoiceMapping
from src.xiangta.services.voice_lab_gateway import VoiceLabGateway
from src.xiangta.services.voice_preset_mapping_service import VoicePresetMappingService

FORBIDDEN_KEYS = {
    "voice_id",
    "model_id",
    "sample_rate",
    "bitrate",
    "api_key",
    "minimax_api_key",
    "mimo_api_key",
    "coreBindingKey",
    "core_binding_key",
    "coreProfileId",
    "core_profile_id",
    "profile_id",
    "provider",
    "model",
    "provider_voice_id",
    "binding_id",
    "params_json",
}

VALID_PAYLOAD = {
    "text": "想念你",
    "voicePreset": "female-gentle",
    "tone": "gentle",
    "recipient": "lover",
    "scene": "miss",
}


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _collect_keys(obj, seen=None):
    if seen is None:
        seen = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            seen.add(k)
            _collect_keys(v, seen)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, seen)
    return seen


async def _fake_generate_tts(self, *, text, target, tone, scene, style=None, metadata=None):
    _ = (text, target, tone, scene, style, metadata)
    return {
        "taskId": "job_123",
        "status": "completed",
        "audioUrl": "/api/voice/assets/audio_123/download",
        "durationMs": 1800,
        "message": None,
        "contract": {
            "voicePresetId": "female-gentle",
            "tone": "gentle",
            "toneHint": "soft",
            "scene": "miss",
            "mode": "core_render_mock",
        },
    }


async def _fake_generate_tts_with_profile(self, *, text, target, tone, scene, style=None, metadata=None):
    _ = (text, tone, scene, style, metadata)
    assert target.provider is None, "profileId path should use provider=None for Core default"
    assert target.profile_id == "deep_night_programmer"
    return {
        "taskId": "job_profile_456",
        "status": "completed",
        "audioUrl": "/api/voice/assets/profile_audio_456/download",
        "durationMs": 2000,
        "message": None,
        "contract": {
            "voicePresetId": "female-gentle",
            "tone": "gentle",
            "toneHint": "soft",
            "scene": "miss",
            "mode": "core_render_mock",
            "profileId": "deep_night_programmer",
        },
    }


def _allow_configured_voice_mapping(monkeypatch):
    def fake_resolve(self, voice_preset_id):
        assert voice_preset_id == "female-gentle"
        return ProductVoiceMapping(
            id="female-gentle",
            label="温柔女声",
            desc="适合想念、晚安、轻声表达",
            gender_style="female",
            suitable_recipients=["lover", "friend"],
            recommended_scenes=["miss", "night"],
            default_tone="gentle",
            enabled=True,
            sort_order=10,
            core_profile_id="deep_night_programmer",
            provider_policy="mock",
            render_overrides={},
            notes=None,
        )

    monkeypatch.setattr(VoicePresetMappingService, "resolve", fake_resolve)


class TestTtsHappyPath:
    def test_status_200(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_ok_true(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.json()["ok"] is True

    def test_has_safe_contract(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        data = client.post("/api/xiangta/tts", json=VALID_PAYLOAD).json()["data"]
        assert data["contract"]["voicePresetId"] == "female-gentle"
        assert data["contract"]["tone"] == "gentle"
        assert data["contract"]["scene"] == "miss"
        assert data["contract"]["mode"] == "core_render_mock"

    def test_old_request_field_voice_preset_still_works(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.status_code == 200
        assert r.json()["data"]["voicePreset"] == "female-gentle"

    def test_response_does_not_expose_core_fields(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        body = client.post("/api/xiangta/tts", json=VALID_PAYLOAD).json()
        bad = _collect_keys(body) & FORBIDDEN_KEYS
        assert not bad, f"POST /tts 响应包含禁止字段：{bad}"

    def test_audio_url_and_duration_are_mapped(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        data = client.post("/api/xiangta/tts", json=VALID_PAYLOAD).json()["data"]
        assert data["audioUrl"] == "/api/voice/assets/audio_123/download"
        assert data["durationMs"] == 1800
        assert data["status"] == "completed"

    def test_tts_with_profile_id_uses_direct_profile_path(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts_with_profile)
        payload = {**VALID_PAYLOAD, "profileId": "deep_night_programmer"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["status"] == "completed"
        assert data["audioUrl"] == "/api/voice/assets/profile_audio_456/download"

    def test_tts_without_profile_id_uses_voice_preset_mapping_path(self, client, monkeypatch):
        """Without profileId, should still use voicePreset mapping path (backward compatible)."""
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_tts_profile_id_omitted_from_response(self, client, monkeypatch):
        """profileId is an input field, not exposed in output."""
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        body = client.post("/api/xiangta/tts", json={**VALID_PAYLOAD, "profileId": "test_profile"}).json()
        bad = _collect_keys(body) & {"profileId", "profile_id", "provider_voice_id", "binding_id"}
        assert not bad


# ── B9: /api/xiangta/core/profiles tests ─────────────────────────────────────────

class TestCoreProfilesApi:
    def test_returns_200_without_core_configured(self, client):
        """未配置 Core 时返回空列表，不 500。"""
        r = client.get("/api/xiangta/core/profiles")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["data"]["profiles"] == []
        assert data["data"]["total"] == 0
        assert data["data"]["source"] == "not_integrated"

    def test_response_no_forbidden_fields_without_core(self, client):
        """未配置 Core 时响应不包含 forbidden fields。"""
        body = client.get("/api/xiangta/core/profiles").json()
        bad = _collect_keys(body) & FORBIDDEN_KEYS
        assert not bad, f"响应包含禁止字段：{bad}"

    def test_profiles_schema_has_expected_fields(self, client):
        """验证响应 schema 包含所有安全字段。"""
        r = client.get("/api/xiangta/core/profiles")
        data = r.json()["data"]
        assert "profiles" in data
        assert "total" in data
        assert "source" in data


class TestValidationAndBusinessErrors:
    def test_invalid_voice_preset_returns_422(self, client, monkeypatch):
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        payload = {**VALID_PAYLOAD, "voicePreset": "nonexistent-voice"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_invalid_tone_returns_422(self, client, monkeypatch):
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        payload = {**VALID_PAYLOAD, "tone": "nonexistent-tone"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_disabled_voice_preset_returns_400(self, client, monkeypatch):
        from src.xiangta.services import voice_preset_mapping_service as service_module
        from src.xiangta.services.voice_preset_mapping_service import VoicePresetDisabled

        def broken_resolve(self, *args, **kwargs):
            raise VoicePresetDisabled("voicePreset 'male-mature' 已禁用")

        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        monkeypatch.setattr(service_module.VoicePresetMappingService, "resolve", broken_resolve)
        payload = {**VALID_PAYLOAD, "voicePreset": "male-mature"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 400
        assert r.json()["ok"] is False

    def test_disabled_tone_returns_400(self, client, monkeypatch):
        from src.xiangta.services import tone_preset_service as service_module
        from src.xiangta.services.tone_preset_service import TonePresetDisabled

        def broken_resolve(self, *args, **kwargs):
            raise TonePresetDisabled("tone 'bedtime' 已禁用")

        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        monkeypatch.setattr(service_module.TonePresetService, "resolve", broken_resolve)
        payload = {**VALID_PAYLOAD, "tone": "bedtime"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 400
        assert r.json()["ok"] is False

    def test_unconfigured_voice_preset_returns_400_without_core_call(self, client, monkeypatch):
        async def fail_if_called(*args, **kwargs):
            raise AssertionError("Gateway must not be called when coreProfileId is not configured")

        monkeypatch.setattr(VoiceLabGateway, "generate_tts", fail_if_called)

        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)

        assert r.status_code == 400
        assert r.json()["ok"] is False
