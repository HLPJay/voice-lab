"""
P17-XIANGTA-B3 — Bootstrap API 集成测试

验证：
  - GET /api/xiangta/bootstrap 返回 200 + 正确结构
  - GET /api/xiangta/provider/status 返回 200 + not_integrated (默认 no http_client)
  - 带 fake gateway 时 providerStatus.kind == "ok"
  - 响应不包含底层 Provider 参数
  - 未实现接口返回 501
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.services.product_service import ProductService
from src.xiangta.services.provider_status_service import ProviderStatusService
from src.xiangta.services.voice_lab_gateway import VoiceLabGateway

FORBIDDEN_KEYS = {
    "voice_id", "model_id", "sample_rate", "bitrate",
    "api_key", "minimax_api_key", "mimo_api_key",
    "core_binding_key", "coreBindingKey", "coreProfileId",
    "core_profile_id", "profile_id", "provider", "model",
    "provider_voice_id", "binding_id", "params_json",
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

    def test_voice_presets_hide_core_fields(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        for vp in data["voicePresets"]:
            forbidden = {
                "core_binding_key", "coreBindingKey", "coreProfileId",
                "core_profile_id", "profile_id", "provider", "model",
                "provider_voice_id", "binding_id", "params_json",
            }
            assert forbidden.isdisjoint(vp.keys()), (
                f"voicePreset {vp.get('id')} 暴露了 Core 字段：{forbidden & set(vp.keys())}"
            )

    def test_voice_presets_use_public_projection_fields(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        for vp in data["voicePresets"]:
            assert "id" in vp
            assert "label" in vp
            assert "desc" in vp
            assert "defaultTone" in vp
            assert "enabled" in vp

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

    def test_tone_presets_hide_core_fields(self, client):
        data = client.get("/api/xiangta/bootstrap").json()["data"]
        forbidden = {
            "coreProfileId", "core_profile_id", "profile_id",
            "provider", "model", "provider_voice_id", "params_json",
        }
        for tone in data["tonePresets"]:
            assert forbidden.isdisjoint(tone.keys())


# ── Admin fields hidden from user-facing bootstrap ───────────────────────────

class TestBootstrapHidesAdminFields:

    def test_bootstrap_does_not_expose_core_profile_id(self, client):
        body = client.get("/api/xiangta/bootstrap").json()
        keys = _collect_keys(body)
        assert "coreProfileId" not in keys

    def test_bootstrap_does_not_expose_provider_policy(self, client):
        body = client.get("/api/xiangta/bootstrap").json()
        keys = _collect_keys(body)
        assert "providerPolicy" not in keys

    def test_bootstrap_does_not_expose_render_overrides(self, client):
        body = client.get("/api/xiangta/bootstrap").json()
        keys = _collect_keys(body)
        assert "renderOverrides" not in keys

    def test_bootstrap_does_not_expose_sort_order(self, client):
        body = client.get("/api/xiangta/bootstrap").json()
        keys = _collect_keys(body)
        assert "sortOrder" not in keys


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


# ── GET /api/xiangta/provider/status with fake gateway ───────────────────────

class FakeGetResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeCoreStatusClient:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    async def get(self, path: str):
        self.requests.append(("GET", path))
        return FakeGetResponse(self.payload)


_AVAILABLE_PAYLOAD = {
    "provider_status": {
        "state": "available",
        "category": "ok",
        "label": "正常",
        "detail": None,
        "action_hint": "最近调用成功",
    }
}


@pytest.fixture(scope="function")
def client_with_gateway(monkeypatch):
    fake_core_client = FakeCoreStatusClient(_AVAILABLE_PAYLOAD)
    gateway = VoiceLabGateway(http_client=fake_core_client)
    provider_status_svc = ProviderStatusService(gateway=gateway)
    service = ProductService(
        bootstrap=MagicMock(**{"get_bootstrap": AsyncMock(return_value={})}),
        provider_status=provider_status_svc,
    )

    import src.xiangta.api.routes as routes_module
    monkeypatch.setattr(routes_module, "create_product_service", lambda: service)

    app = FastAPI()
    app.include_router(router)
    return TestClient(app), fake_core_client


class TestProviderStatusWithGateway:

    def test_status_200(self, client_with_gateway):
        client, _ = client_with_gateway
        r = client.get("/api/xiangta/provider/status")
        assert r.status_code == 200

    def test_ok_true(self, client_with_gateway):
        client, _ = client_with_gateway
        r = client.get("/api/xiangta/provider/status")
        assert r.json()["ok"] is True

    def test_kind_ok_from_available_gateway(self, client_with_gateway):
        client, _ = client_with_gateway
        data = client.get("/api/xiangta/provider/status").json()["data"]
        assert data["kind"] == "ok"

    def test_called_runtime_status_path(self, client_with_gateway):
        client, fake_core_client = client_with_gateway
        client.get("/api/xiangta/provider/status")
        assert ("GET", "/api/voice/runtime/status") in fake_core_client.requests

    def test_no_forbidden_keys(self, client_with_gateway):
        client, _ = client_with_gateway
        body = client.get("/api/xiangta/provider/status").json()
        keys = _collect_keys(body)
        bad = keys & FORBIDDEN_KEYS
        assert not bad, f"gateway status 响应包含禁止字段：{bad}"

    def test_degraded_when_gateway_fails(self, monkeypatch):
        class ErrorGetClient:
            async def get(self, path: str):
                raise RuntimeError("simulated core failure")

        gateway = VoiceLabGateway(http_client=ErrorGetClient())
        provider_status_svc = ProviderStatusService(gateway=gateway)
        service = ProductService(
            bootstrap=MagicMock(**{"get_bootstrap": AsyncMock(return_value={})}),
            provider_status=provider_status_svc,
        )

        import src.xiangta.api.routes as routes_module
        monkeypatch.setattr(routes_module, "create_product_service", lambda: service)

        app = FastAPI()
        app.include_router(router)
        c = TestClient(app)
        r = c.get("/api/xiangta/provider/status")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["kind"] == "degraded"


# ── 未实现接口返回 501 ────────────────────────────────────────────────────────

class TestUnimplementedRoutes:

    def test_suggestions_returns_200(self, client):
        r = client.post("/api/xiangta/suggestions", json={
            "recipient": "lover", "scene": "miss", "rawText": "我今天很想你"
        })
        assert r.status_code == 200

    def test_create_letter_returns_501(self, client):
        r = client.post("/api/xiangta/letters", json={})
        assert r.status_code == 501

    def test_list_letters_returns_501(self, client):
        r = client.get("/api/xiangta/letters")
        assert r.status_code == 501
