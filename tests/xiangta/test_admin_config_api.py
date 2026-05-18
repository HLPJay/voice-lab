"""
P17-XIANGTA-ADMIN-CONFIG-B4-1 — Admin Config API 集成测试（只读）

验证：
  - GET /api/xiangta/admin/config 返回完整配置快照（含 coreProfileId）
  - GET /api/xiangta/admin/voice-mappings 返回带 Core 字段的映射列表
  - GET /api/xiangta/admin/tone-presets 返回带 renderOverrides 的音调列表
  - Admin 接口不泄露 api_key / provider_voice_id / binding_id / params_json / model
  - 用户端 bootstrap 仍不暴露 coreProfileId / providerPolicy / renderOverrides
"""
import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router

ADMIN_FORBIDDEN_KEYS = {
    "api_key",
    "minimax_api_key",
    "mimo_api_key",
    "provider_api_key",
    "provider_voice_id",
    "binding_id",
    "params_json",
    "model",
    "voice_id",
    "model_id",
}


ADMIN_HEADERS = {"X-XiangTa-Admin-Token": "test-admin-token"}

os.environ.setdefault("XIANGTA_ADMIN_ENABLED", "true")
os.environ.setdefault("XIANGTA_ADMIN_TOKEN", "test-admin-token")
os.environ.setdefault("XIANGTA_TEST_AUTO_ADMIN_HEADER", "1")

_ORIGINAL_REQUEST = TestClient.request


def _patched_request(self, method, url, *args, **kwargs):
    headers = dict(kwargs.get("headers") or {})
    if (
        os.environ.get("XIANGTA_TEST_AUTO_ADMIN_HEADER", "1") == "1"
        and "/api/xiangta/admin/" in str(url)
        and "X-XiangTa-Admin-Token" not in headers
    ):
        token = os.environ.get("XIANGTA_ADMIN_TOKEN")
        if token:
            headers["X-XiangTa-Admin-Token"] = token
            kwargs["headers"] = headers
    return _ORIGINAL_REQUEST(self, method, url, *args, **kwargs)


if TestClient.request is not _patched_request:
    TestClient.request = _patched_request


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture(autouse=True)
def _admin_env(monkeypatch):
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")
    monkeypatch.setenv("XIANGTA_ADMIN_TOKEN", "test-admin-token")


def _collect_keys(obj, seen=None) -> set[str]:
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


# ── GET /api/xiangta/admin/config ─────────────────────────────────────────────

class TestAdminConfig:

    def test_status_200(self, client):
        r = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_ok_true(self, client):
        assert client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["ok"] is True

    def test_has_data(self, client):
        assert "data" in client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()

    def test_has_voice_mappings(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        assert "voiceMappings" in data
        assert isinstance(data["voiceMappings"], list)
        assert len(data["voiceMappings"]) > 0

    def test_has_tone_presets(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        assert "tonePresets" in data
        assert isinstance(data["tonePresets"], list)
        assert len(data["tonePresets"]) > 0

    def test_has_recipients(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        assert "recipients" in data
        assert len(data["recipients"]) > 0

    def test_has_scenes(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        assert "scenes" in data
        assert len(data["scenes"]) > 0

    def test_has_limits(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        assert "limits" in data
        assert "maxRawTextChars" in data["limits"]
        assert "maxTtsChars" in data["limits"]
        assert "maxSuggestions" in data["limits"]

    def test_voice_mappings_expose_core_profile_id(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        for vm in data["voiceMappings"]:
            assert "coreProfileId" in vm, f"voiceMapping {vm.get('id')} missing coreProfileId"
            assert vm["coreProfileId"]

    def test_voice_mappings_expose_provider_policy(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        for vm in data["voiceMappings"]:
            assert "providerPolicy" in vm, f"voiceMapping {vm.get('id')} missing providerPolicy"

    def test_voice_mappings_expose_render_overrides(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        for vm in data["voiceMappings"]:
            assert "renderOverrides" in vm, f"voiceMapping {vm.get('id')} missing renderOverrides"
            assert isinstance(vm["renderOverrides"], dict)

    def test_voice_mappings_required_fields(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        for vm in data["voiceMappings"]:
            assert "id" in vm
            assert "label" in vm
            assert "desc" in vm
            assert "defaultTone" in vm
            assert "enabled" in vm
            assert "sortOrder" in vm

    def test_tone_presets_have_render_overrides(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        for tp in data["tonePresets"]:
            assert "renderOverrides" in tp
            assert isinstance(tp["renderOverrides"], dict)

    def test_tone_presets_have_style_hint(self, client):
        data = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()["data"]
        for tp in data["tonePresets"]:
            assert "styleHint" in tp

    def test_no_admin_forbidden_keys(self, client):
        body = client.get("/api/xiangta/admin/config", headers=ADMIN_HEADERS).json()
        keys = _collect_keys(body)
        bad = keys & ADMIN_FORBIDDEN_KEYS
        assert not bad, f"admin/config 响应包含禁止字段：{bad}"


# ── GET /api/xiangta/admin/voice-mappings ─────────────────────────────────────

class TestAdminVoiceMappings:

    def test_status_200(self, client):
        r = client.get("/api/xiangta/admin/voice-mappings", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_ok_true(self, client):
        assert client.get("/api/xiangta/admin/voice-mappings", headers=ADMIN_HEADERS).json()["ok"] is True

    def test_data_is_list(self, client):
        data = client.get("/api/xiangta/admin/voice-mappings", headers=ADMIN_HEADERS).json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0

    def test_items_have_core_profile_id(self, client):
        data = client.get("/api/xiangta/admin/voice-mappings", headers=ADMIN_HEADERS).json()["data"]
        for item in data:
            assert "coreProfileId" in item
            assert item["coreProfileId"]

    def test_items_have_provider_policy(self, client):
        data = client.get("/api/xiangta/admin/voice-mappings", headers=ADMIN_HEADERS).json()["data"]
        for item in data:
            assert "providerPolicy" in item

    def test_items_have_render_overrides(self, client):
        data = client.get("/api/xiangta/admin/voice-mappings", headers=ADMIN_HEADERS).json()["data"]
        for item in data:
            assert "renderOverrides" in item
            assert isinstance(item["renderOverrides"], dict)

    def test_no_forbidden_keys(self, client):
        body = client.get("/api/xiangta/admin/voice-mappings", headers=ADMIN_HEADERS).json()
        keys = _collect_keys(body)
        bad = keys & ADMIN_FORBIDDEN_KEYS
        assert not bad, f"admin/voice-mappings 响应包含禁止字段：{bad}"


# ── GET /api/xiangta/admin/tone-presets ──────────────────────────────────────

class TestAdminTonePresets:

    def test_status_200(self, client):
        r = client.get("/api/xiangta/admin/tone-presets", headers=ADMIN_HEADERS)
        assert r.status_code == 200

    def test_ok_true(self, client):
        assert client.get("/api/xiangta/admin/tone-presets", headers=ADMIN_HEADERS).json()["ok"] is True

    def test_data_is_list(self, client):
        data = client.get("/api/xiangta/admin/tone-presets", headers=ADMIN_HEADERS).json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0

    def test_items_have_render_overrides(self, client):
        data = client.get("/api/xiangta/admin/tone-presets", headers=ADMIN_HEADERS).json()["data"]
        for item in data:
            assert "renderOverrides" in item
            assert isinstance(item["renderOverrides"], dict)

    def test_items_have_style_hint(self, client):
        data = client.get("/api/xiangta/admin/tone-presets", headers=ADMIN_HEADERS).json()["data"]
        for item in data:
            assert "styleHint" in item

    def test_items_have_sort_order(self, client):
        data = client.get("/api/xiangta/admin/tone-presets", headers=ADMIN_HEADERS).json()["data"]
        for item in data:
            assert "sortOrder" in item

    def test_no_forbidden_keys(self, client):
        body = client.get("/api/xiangta/admin/tone-presets", headers=ADMIN_HEADERS).json()
        keys = _collect_keys(body)
        bad = keys & ADMIN_FORBIDDEN_KEYS
        assert not bad, f"admin/tone-presets 响应包含禁止字段：{bad}"
