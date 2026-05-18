"""
Tests for C7 TTS Task API.

Covers:
1. POST /api/xiangta/tts/tasks returns 200, ok=true, taskId, status, pollUrl
2. POST then GET returns completed task
3. GET response contains audioUrl/durationMs/charCount/voicePreset/tone
4. GET missing task returns 404 flat error (no detail)
5. task API response doesn't expose forbidden provider/core fields
6. business error creates failed task (not 500)
7. failed task GET returns errorKind/message/retryable
8. clear_tts_tasks_for_tests clears task state
9. old POST /api/xiangta/tts still works (smoke)
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.config.product_config_models import ProductVoiceMapping
from src.xiangta.services.tts_task_service import clear_tts_tasks_for_tests
from src.xiangta.services.voice_lab_gateway import VoiceLabGateway
from src.xiangta.services.voice_preset_mapping_service import VoicePresetMappingService

FORBIDDEN_KEYS = {
    "voice_id", "model_id", "sample_rate", "bitrate",
    "api_key", "minimax_api_key", "mimo_api_key",
    "coreBindingKey", "core_binding_key",
    "coreProfileId", "core_profile_id", "profile_id",
    "provider", "model", "provider_voice_id",
    "binding_id", "params_json",
}

VALID_PAYLOAD = {
    "text": "想念你",
    "voicePreset": "female-gentle",
    "tone": "gentle",
    "recipient": "lover",
    "scene": "miss",
}


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


async def _fake_generate_tts_failure(self, *, text, target, tone, scene, style=None, metadata=None):
    from src.xiangta.services.error_translator import NoProviderError
    raise NoProviderError()


def _allow_configured_voice_mapping(monkeypatch):
    def fake_resolve(self, voice_preset_id):
        assert voice_preset_id == "female-gentle"
        return ProductVoiceMapping(
            id="female-gentle", label="温柔女声", desc="适合想念",
            gender_style="female", suitable_recipients=["lover", "friend"],
            recommended_scenes=["miss", "night"], default_tone="gentle",
            enabled=True, sort_order=10,
            core_profile_id="deep_night_programmer",
            provider_policy="mock", render_overrides={}, notes=None,
        )
    monkeypatch.setattr(VoicePresetMappingService, "resolve", fake_resolve)


@pytest.fixture(autouse=True)
def clean_tasks():
    clear_tts_tasks_for_tests()
    yield
    clear_tts_tasks_for_tests()


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestCreateTtsTask:
    def test_returns_200_and_ok_true(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts/tasks", json=VALID_PAYLOAD)
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_response_has_task_id_status_poll_url(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts/tasks", json=VALID_PAYLOAD)
        data = r.json()["data"]
        assert "taskId" in data
        assert data["taskId"].startswith("TTS_")
        assert data["status"] in ("completed", "failed")
        assert "/api/xiangta/tts/tasks/" in data["pollUrl"]

    def test_post_then_get_returns_completed_task(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts/tasks", json=VALID_PAYLOAD)
        task_id = r.json()["data"]["taskId"]

        r2 = client.get(f"/api/xiangta/tts/tasks/{task_id}")
        assert r2.status_code == 200
        task = r2.json()["data"]
        assert task["status"] == "completed"
        assert task["audioUrl"] == "/api/voice/assets/audio_123/download"
        assert task["durationMs"] == 1800
        assert task["charCount"] == len(VALID_PAYLOAD["text"])
        assert task["voicePreset"] == "female-gentle"
        assert task["tone"] == "gentle"
        assert task["message"] is None
        assert task["errorKind"] is None

    def test_get_missing_task_returns_404_flat_error(self, client):
        r = client.get("/api/xiangta/tts/tasks/TTS_nonexistent")
        assert r.status_code == 404
        body = r.json()
        assert body["ok"] is False
        assert body["errorKind"] == "not_found"
        assert "not found" in body["message"].lower()
        assert "detail" not in body

    def test_task_response_no_forbidden_fields(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts/tasks", json=VALID_PAYLOAD)
        task_id = r.json()["data"]["taskId"]
        body = client.get(f"/api/xiangta/tts/tasks/{task_id}").json()
        bad = _collect_keys(body) & FORBIDDEN_KEYS
        assert not bad, f"响应包含禁止字段：{bad}"

    def test_business_error_creates_failed_task_not_500(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts_failure)
        r = client.post("/api/xiangta/tts/tasks", json=VALID_PAYLOAD)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        assert r.json()["data"]["status"] == "failed"

    def test_failed_task_get_returns_error_kind_message_retryable(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts_failure)
        r = client.post("/api/xiangta/tts/tasks", json=VALID_PAYLOAD)
        task_id = r.json()["data"]["taskId"]
        task = client.get(f"/api/xiangta/tts/tasks/{task_id}").json()["data"]
        assert task["status"] == "failed"
        assert task["errorKind"] == "no_provider"
        assert "message" in task
        assert task["retryable"] is True

    def test_clear_tts_tasks_for_tests(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts/tasks", json=VALID_PAYLOAD)
        task_id = r.json()["data"]["taskId"]
        clear_tts_tasks_for_tests()
        r2 = client.get(f"/api/xiangta/tts/tasks/{task_id}")
        assert r2.status_code == 404


class TestOldSyncTtsUnaffected:
    def test_old_post_tts_still_works(self, client, monkeypatch):
        _allow_configured_voice_mapping(monkeypatch)
        monkeypatch.setattr(VoiceLabGateway, "generate_tts", _fake_generate_tts)
        r = client.post("/api/xiangta/tts", json=VALID_PAYLOAD)
        assert r.status_code == 200
        assert r.json()["ok"] is True
