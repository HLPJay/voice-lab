"""
P18-XIANGTA-VOICE-PRESETS-API-C1 — Voice Presets public API tests

验证：
  - GET /api/xiangta/voice-presets 返回 200 + 正确结构
  - 响应只包含公开字段，不含 coreProfileId / providerPolicy / renderOverrides
  - disabled preset 不出现在公开响应中
  - data.total == len(data.presets)
  - data.source == "config"
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router

FORBIDDEN_FIELDS = {
    "coreProfileId",
    "core_profile_id",
    "providerPolicy",
    "provider_policy",
    "renderOverrides",
    "render_overrides",
    "apiKey",
    "api_key",
    "providerVoiceId",
    "provider_voice_id",
    "bindingId",
    "binding_id",
}

PUBLIC_FIELDS = {
    "id",
    "label",
    "desc",
    "genderStyle",
    "suitableRecipients",
    "recommendedScenes",
    "defaultTone",
    "enabled",
}


@pytest.fixture(scope="module")
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _collect_keys(obj: object, seen: set | None = None) -> set[str]:
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


class TestVoicePresetsApi:

    def test_status_200(self, client):
        r = client.get("/api/xiangta/voice-presets")
        assert r.status_code == 200

    def test_ok_true(self, client):
        r = client.get("/api/xiangta/voice-presets")
        assert r.json()["ok"] is True

    def test_data_has_presets(self, client):
        r = client.get("/api/xiangta/voice-presets")
        assert "data" in r.json()
        assert "presets" in r.json()["data"]

    def test_presets_is_list(self, client):
        r = client.get("/api/xiangta/voice-presets")
        assert isinstance(r.json()["data"]["presets"], list)

    def test_data_has_total(self, client):
        r = client.get("/api/xiangta/voice-presets")
        assert "total" in r.json()["data"]

    def test_total_equals_presets_len(self, client):
        r = client.get("/api/xiangta/voice-presets")
        data = r.json()["data"]
        assert data["total"] == len(data["presets"])

    def test_source_is_config(self, client):
        r = client.get("/api/xiangta/voice-presets")
        assert r.json()["data"]["source"] == "config"

    def test_each_preset_has_public_fields(self, client):
        r = client.get("/api/xiangta/voice-presets")
        presets = r.json()["data"]["presets"]
        for p in presets:
            for field in PUBLIC_FIELDS:
                assert field in p, f"preset missing public field: {field}"

    def test_disabled_preset_not_in_response(self, client):
        r = client.get("/api/xiangta/voice-presets")
        presets = r.json()["data"]["presets"]
        # All returned presets must be enabled
        for p in presets:
            assert p.get("enabled") is True, f"disabled preset {p.get('id')} appeared in public response"

    def test_no_forbidden_fields_in_response(self, client):
        r = client.get("/api/xiangta/voice-presets")
        keys = _collect_keys(r.json())
        bad = keys & FORBIDDEN_FIELDS
        assert not bad, f"voice-presets 响应包含禁止字段：{bad}"

    def test_no_core_profile_id_in_any_preset(self, client):
        r = client.get("/api/xiangta/voice-presets")
        for p in r.json()["data"]["presets"]:
            assert "coreProfileId" not in p
            assert "core_profile_id" not in p

    def test_no_provider_policy_in_any_preset(self, client):
        r = client.get("/api/xiangta/voice-presets")
        for p in r.json()["data"]["presets"]:
            assert "providerPolicy" not in p
            assert "provider_policy" not in p

    def test_no_render_overrides_in_any_preset(self, client):
        r = client.get("/api/xiangta/voice-presets")
        for p in r.json()["data"]["presets"]:
            assert "renderOverrides" not in p
            assert "render_overrides" not in p

    def test_no_forbidden_fields_in_json_string(self, client):
        """Verify forbidden fields don't appear even in JSON serialization."""
        r = client.get("/api/xiangta/voice-presets")
        json_str = r.content.decode("utf-8")
        for field in FORBIDDEN_FIELDS:
            assert field not in json_str, f"forbidden field '{field}' found in JSON response"

    def test_presets_have_valid_ids(self, client):
        r = client.get("/api/xiangta/voice-presets")
        for p in r.json()["data"]["presets"]:
            assert p["id"], "preset id must be non-empty"

    def test_presets_have_non_empty_label(self, client):
        r = client.get("/api/xiangta/voice-presets")
        for p in r.json()["data"]["presets"]:
            assert p["label"], "preset label must be non-empty"
