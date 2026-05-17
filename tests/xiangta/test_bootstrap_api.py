"""
P17-XIANGTA-A1 — Bootstrap API 集成测试

使用独立 FastAPI app（不注册到主应用）。
验证：
  - GET /api/xiangta/bootstrap 返回 200 + 正确结构
  - GET /api/xiangta/provider/status 返回 200 + not_integrated
  - 响应不包含底层 Provider 参数
  - 未实现接口返回 501
"""
import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router

FORBIDDEN_KEYS = {
    "voice_id", "model_id", "sample_rate", "bitrate",
    "api_key", "minimax_api_key", "mimo_api_key",
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


# ── GET /api/xiangta/bootstrap ────────────────────────────────────────────────

class TestBootstrap:

    def test_status_200(self, client):
        r = client.get("/api/xiangta/bootstrap")
        assert r.status_code == 200

    def test_ok_true(self, client):
        r = client.get("/api/xiangta/bootstrap")
        assert r.json()["ok"] is True

    def test_has_data(self, client):
        r = client.get("/api/xiangta/bootstrap")
        assert "data" in r.json()

    def test_has_recipients(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert "recipients" in data
        assert len(data["recipients"]) > 0

    def test_has_scenes(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert "scenes" in data
        assert len(data["scenes"]) > 0

    def test_has_styles(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert "styles" in data
        assert len(data["styles"]) >= 3

    def test_has_voice_presets(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert "voicePresets" in data
        assert len(data["voicePresets"]) > 0

    def test_has_tone_presets(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert "tonePresets" in data
        assert len(data["tonePresets"]) > 0

    def test_has_limits(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert "limits" in data
        limits = data["limits"]
        assert "maxRawTextChars" in limits
        assert "maxTtsChars" in limits
        assert "maxSuggestions" in limits

    def test_has_provider_status(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert "providerStatus" in data

    def test_provider_status_kind_not_integrated(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert data["providerStatus"]["kind"] == "not_integrated"

    def test_provider_status_quota_pct_zero(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert data["providerStatus"]["quotaPct"] == 0.0

    def test_no_forbidden_keys_in_response(self, client):
        body = client.get("/api/xiangta/bootstrap").json()
        keys = _collect_keys(body)
        bad = keys & FORBIDDEN_KEYS
        assert not bad, f"bootstrap 响应包含禁止字段：{bad}"

    def test_voice_presets_have_core_binding_key(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        for vp in data["voicePresets"]:
            assert "core_binding_key" in vp, f"voicePreset {vp.get('id')} 缺少 core_binding_key"
            assert vp["core_binding_key"].startswith("xiangta_")

    def test_recipients_have_required_fields(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        for r in data["recipients"]:
            assert "id" in r
            assert "label" in r

    def test_scenes_have_required_fields(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        for s in data["scenes"]:
            assert "id" in s
            assert "label" in s

    def test_styles_have_three_items(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        style_ids = {s["id"] for s in data["styles"]}
        assert style_ids == {"restrained", "gentle", "sincere"}

    def test_limits_max_chars_500(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        assert data["limits"]["maxRawTextChars"] == 500
        assert data["limits"]["maxTtsChars"] == 500

    def test_all_recipients_present(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        ids = {r["id"] for r in data["recipients"]}
        assert ids == {"lover", "family", "friend", "self"}

    def test_all_scenes_present(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        ids = {s["id"] for s in data["scenes"]}
        assert ids == {"miss", "sorry", "thanks", "comfort", "night"}


# ── GET /api/xiangta/provider/status ─────────────────────────────────────────

class TestProviderStatus:

    def test_status_200(self, client):
        r = client.get("/api/xiangta/provider/status")
        assert r.status_code == 200

    def test_ok_true(self, client):
        r = client.get("/api/xiangta/provider/status")
        assert r.json()["ok"] is True

    def test_kind_not_integrated(self, client):
        data = client.get("/api/xiangta/provider/status").json()["data"]
        assert data["kind"] == "not_integrated"

    def test_has_label(self, client):
        data = client.get("/api/xiangta/provider/status").json()["data"]
        assert data["label"]

    def test_has_detail(self, client):
        data = client.get("/api/xiangta/provider/status").json()["data"]
        assert data["detail"]

    def test_quota_pct_zero(self, client):
        data = client.get("/api/xiangta/provider/status").json()["data"]
        assert data["quotaPct"] == 0.0

    def test_no_forbidden_keys(self, client):
        body = client.get("/api/xiangta/provider/status").json()
        keys = _collect_keys(body)
        bad = keys & FORBIDDEN_KEYS
        assert not bad, f"provider/status 响应包含禁止字段：{bad}"


# ── 未实现接口返回 501 ────────────────────────────────────────────────────────

class TestUnimplementedRoutes:

    def test_suggestions_returns_501(self, client):
        r = client.post("/api/xiangta/suggestions", json={
            "recipient": "lover", "scene": "miss", "rawText": "测试"
        })
        assert r.status_code == 501

    def test_create_letter_returns_501(self, client):
        r = client.post("/api/xiangta/letters", json={})
        assert r.status_code == 501

    def test_list_letters_returns_501(self, client):
        r = client.get("/api/xiangta/letters")
        assert r.status_code == 501
