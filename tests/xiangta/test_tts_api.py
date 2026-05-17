"""
P17-XIANGTA-PRODUCT-CONFIG-B1-3 — POST /api/xiangta/tts API 层测试
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router

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


class TestTtsDryRunHappyPath:
    def test_status_200(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.status_code == 200

    def test_ok_true(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.json()["ok"] is True

    def test_has_safe_contract(self, client):
        data = client.post("/api/xiangta/tts", json=VALID_PAYLOAD).json()["data"]
        assert data["contract"]["voicePresetId"] == "female-gentle"
        assert data["contract"]["tone"] == "gentle"
        assert data["contract"]["scene"] == "miss"
        assert data["contract"]["mode"] == "dry_run"

    def test_old_request_field_voice_preset_still_works(self, client):
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.status_code == 200
        assert r.json()["data"]["voicePreset"] == "female-gentle"

    def test_response_does_not_expose_core_fields(self, client):
        body = client.post("/api/xiangta/tts", json=VALID_PAYLOAD).json()
        bad = _collect_keys(body) & FORBIDDEN_KEYS
        assert not bad, f"POST /tts 响应包含禁止字段：{bad}"

    def test_task_id_starts_with_dryrun(self, client):
        data = client.post("/api/xiangta/tts", json=VALID_PAYLOAD).json()["data"]
        assert data["taskId"].startswith("dryrun_")


class TestValidationAndBusinessErrors:
    def test_invalid_voice_preset_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "voicePreset": "nonexistent-voice"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_invalid_tone_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "tone": "nonexistent-tone"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 422

    def test_disabled_voice_preset_returns_400(self, client, monkeypatch):
        from src.xiangta.services import voice_preset_mapping_service as service_module
        from src.xiangta.services.voice_preset_mapping_service import VoicePresetDisabled

        def broken_resolve(self, *args, **kwargs):
            raise VoicePresetDisabled("voicePreset 'male-mature' 已禁用")

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

        monkeypatch.setattr(service_module.TonePresetService, "resolve", broken_resolve)
        payload = {**VALID_PAYLOAD, "tone": "bedtime"}
        r = client.post("/api/xiangta/tts", json=payload)
        assert r.status_code == 400
        assert r.json()["ok"] is False
