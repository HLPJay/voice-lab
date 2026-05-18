"""
P17-XIANGTA-ADMIN-CONFIG-B4-3 — Admin Config Write API 集成测试

验证：
  - PUT  /api/xiangta/admin/voice-mappings/{id}
  - PATCH /api/xiangta/admin/voice-mappings/{id}/enabled
  - PUT  /api/xiangta/admin/tone-presets/{id}
  - PATCH /api/xiangta/admin/tone-presets/{id}/enabled
  - 404 on unknown id
  - 422 on validation error
  - 所有写操作使用 tmp_path，不修改真实 JSON
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.config.product_config_writer import ProductConfigWriter
from src.xiangta.services.admin_config_service import AdminConfigService
from src.xiangta.services.product_service import ProductService
from src.xiangta.services.provider_status_service import ProviderStatusService

import src.xiangta.api.routes as routes_module

_VOICE_MAPPINGS = [
    {
        "id": "vm-1",
        "label": "测试声音",
        "desc": "测试描述",
        "genderStyle": "female",
        "suitableRecipients": ["lover"],
        "recommendedScenes": ["miss"],
        "defaultTone": "gentle",
        "enabled": True,
        "sortOrder": 10,
        "coreProfileId": "core-profile-001",
        "providerPolicy": "default",
        "renderOverrides": {},
        "notes": None,
    }
]

_TONE_PRESETS = [
    {
        "id": "tp-1",
        "label": "克制",
        "desc": "少一点情绪",
        "style_hint": "calm",
        "enabled": True,
    }
]

_ADMIN_HEADERS = {"X-XiangTa-Admin-Token": "test-admin-token"}


@pytest.fixture(autouse=True)
def _admin_env(monkeypatch):
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")
    monkeypatch.setenv("XIANGTA_ADMIN_TOKEN", "test-admin-token")


@pytest.fixture
def write_client(tmp_path, monkeypatch):
    (tmp_path / "voice_mappings.json").write_text(
        json.dumps(_VOICE_MAPPINGS, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "tone_presets.json").write_text(
        json.dumps(_TONE_PRESETS, ensure_ascii=False), encoding="utf-8"
    )

    writer = ProductConfigWriter(config_dir=tmp_path)
    admin_svc = AdminConfigService(writer=writer)
    provider_status_svc = ProviderStatusService(gateway=None)
    service = ProductService(
        bootstrap=MagicMock(**{"get_bootstrap": AsyncMock(return_value={})}),
        provider_status=provider_status_svc,
        admin_config_service=admin_svc,
    )

    monkeypatch.setattr(routes_module, "create_product_service", lambda: service)

    app = FastAPI()
    app.include_router(router)

    class AdminTestClient(TestClient):
        def put(self, url, *args, **kwargs):
            kwargs.setdefault("headers", _ADMIN_HEADERS)
            return super().put(url, *args, **kwargs)

        def patch(self, url, *args, **kwargs):
            kwargs.setdefault("headers", _ADMIN_HEADERS)
            return super().patch(url, *args, **kwargs)

        def get(self, url, *args, **kwargs):
            kwargs.setdefault("headers", _ADMIN_HEADERS)
            return super().get(url, *args, **kwargs)

    return AdminTestClient(app), tmp_path


# ── PUT /admin/voice-mappings/{id} ────────────────────────────────────────────

class TestUpdateVoiceMapping:

    def test_status_200(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"label": "新标签"})
        assert r.status_code == 200

    def test_ok_true(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"label": "新标签"})
        assert r.json()["ok"] is True

    def test_returns_updated_label(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"label": "新标签"})
        assert r.json()["data"]["label"] == "新标签"

    def test_persists_to_file(self, write_client):
        client, tmp_path = write_client
        client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"label": "持久化"})
        saved = json.loads((tmp_path / "voice_mappings.json").read_text(encoding="utf-8"))
        assert saved[0]["label"] == "持久化"

    def test_update_core_profile_id(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"coreProfileId": "real-profile-xyz"})
        assert r.json()["data"]["coreProfileId"] == "real-profile-xyz"

    def test_update_render_overrides(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"renderOverrides": {"speed": 1.1}})
        assert r.json()["data"]["renderOverrides"] == {"speed": 1.1}

    def test_not_found_returns_404(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/no-such-id", json={"label": "x"})
        assert r.status_code == 404
        assert r.json()["ok"] is False

    def test_forbidden_field_returns_422(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"api_key": "secret"})
        assert r.status_code == 422

    def test_invalid_render_override_returns_422(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"renderOverrides": {"bad_key": 1}})
        assert r.status_code == 422
        assert r.json()["ok"] is False

    def test_invalid_core_profile_id_placeholder_returns_422(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"coreProfileId": "<placeholder>"})
        assert r.status_code == 422

    def test_empty_label_returns_422(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"label": "  "})
        assert r.status_code == 422

    def test_response_data_has_id(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/voice-mappings/vm-1", json={"label": "x"})
        assert r.json()["data"]["id"] == "vm-1"


# ── PATCH /admin/voice-mappings/{id}/enabled ──────────────────────────────────

class TestToggleVoiceMappingEnabled:

    def test_disable_returns_200(self, write_client):
        client, _ = write_client
        r = client.patch("/api/xiangta/admin/voice-mappings/vm-1/enabled", json={"enabled": False})
        assert r.status_code == 200

    def test_disable_sets_enabled_false(self, write_client):
        client, _ = write_client
        r = client.patch("/api/xiangta/admin/voice-mappings/vm-1/enabled", json={"enabled": False})
        assert r.json()["data"]["enabled"] is False

    def test_re_enable(self, write_client):
        client, _ = write_client
        client.patch("/api/xiangta/admin/voice-mappings/vm-1/enabled", json={"enabled": False})
        r = client.patch("/api/xiangta/admin/voice-mappings/vm-1/enabled", json={"enabled": True})
        assert r.json()["data"]["enabled"] is True

    def test_not_found_returns_404(self, write_client):
        client, _ = write_client
        r = client.patch("/api/xiangta/admin/voice-mappings/bad-id/enabled", json={"enabled": False})
        assert r.status_code == 404


# ── PUT /admin/tone-presets/{id} ──────────────────────────────────────────────

class TestUpdateTonePreset:

    def test_status_200(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"label": "新克制"})
        assert r.status_code == 200

    def test_ok_true(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"label": "x"})
        assert r.json()["ok"] is True

    def test_returns_updated_label(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"label": "新克制"})
        assert r.json()["data"]["label"] == "新克制"

    def test_update_render_overrides(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"renderOverrides": {"speed": 0.8}})
        assert r.json()["data"]["renderOverrides"] == {"speed": 0.8}

    def test_update_style_hint(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"styleHint": "bright"})
        assert r.json()["data"]["styleHint"] == "bright"

    def test_persists_to_file(self, write_client):
        client, tmp_path = write_client
        client.put("/api/xiangta/admin/tone-presets/tp-1", json={"label": "保存"})
        saved = json.loads((tmp_path / "tone_presets.json").read_text(encoding="utf-8"))
        assert saved[0]["label"] == "保存"

    def test_not_found_returns_404(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/no-such-id", json={"label": "x"})
        assert r.status_code == 404

    def test_forbidden_field_returns_422(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"coreProfileId": "x"})
        assert r.status_code == 422

    def test_invalid_render_override_returns_422(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"renderOverrides": {"illegal": 1}})
        assert r.status_code == 422

    def test_empty_label_returns_422(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"label": ""})
        assert r.status_code == 422

    def test_response_data_has_id(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"label": "x"})
        assert r.json()["data"]["id"] == "tp-1"

    def test_response_has_sort_order(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"label": "x"})
        assert "sortOrder" in r.json()["data"]

    def test_response_has_render_overrides(self, write_client):
        client, _ = write_client
        r = client.put("/api/xiangta/admin/tone-presets/tp-1", json={"label": "x"})
        assert "renderOverrides" in r.json()["data"]


# ── PATCH /admin/tone-presets/{id}/enabled ────────────────────────────────────

class TestToggleTonePresetEnabled:

    def test_disable_returns_200(self, write_client):
        client, _ = write_client
        r = client.patch("/api/xiangta/admin/tone-presets/tp-1/enabled", json={"enabled": False})
        assert r.status_code == 200

    def test_disable_sets_enabled_false(self, write_client):
        client, _ = write_client
        r = client.patch("/api/xiangta/admin/tone-presets/tp-1/enabled", json={"enabled": False})
        assert r.json()["data"]["enabled"] is False

    def test_re_enable(self, write_client):
        client, _ = write_client
        client.patch("/api/xiangta/admin/tone-presets/tp-1/enabled", json={"enabled": False})
        r = client.patch("/api/xiangta/admin/tone-presets/tp-1/enabled", json={"enabled": True})
        assert r.json()["data"]["enabled"] is True

    def test_not_found_returns_404(self, write_client):
        client, _ = write_client
        r = client.patch("/api/xiangta/admin/tone-presets/bad-id/enabled", json={"enabled": True})
        assert r.status_code == 404
