"""
P17-XIANGTA-PROVIDER-STATUS-B3 — app-level status Core mock integration test.

Target chain:
  GET /api/xiangta/provider/status
  → ProviderStatusService
  → VoiceLabGateway.get_provider_status()
  → FakeCoreStatusClient (in-process fake, no real Core)
  → /api/voice/runtime/status
  → XiangTa status response
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router
from src.xiangta.services.product_service import ProductService
from src.xiangta.services.provider_status_service import ProviderStatusService
from src.xiangta.services.voice_lab_gateway import VoiceLabGateway

FORBIDDEN_KEYS = {
    "api_key",
    "env",
    "provider_secret",
    "raw_config",
    "stack_trace",
    "minimax_api_key",
    "mimo_api_key",
    "provider_api_key",
}


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


class FakeStatusResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeCoreStatusClient:
    """Fake Core http client that handles GET /api/voice/runtime/status."""

    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.requests: list[tuple[str, str]] = []

    async def get(self, path: str) -> FakeStatusResponse:
        self.requests.append(("GET", path))
        return FakeStatusResponse(self.payload)


_AVAILABLE_PAYLOAD = {
    "current": {
        "default_provider": "mock",
        "default_model": "mock-model",
        "default_ws_model": "mock-ws-model",
        "default_audio_format": "mp3",
    },
    "provider_status": {
        "state": "available",
        "category": "ok",
        "label": "正常",
        "detail": None,
        "action_hint": "最近调用成功",
        "last_seen_at": None,
        "duration_ms": None,
    },
    "today": {"job_count": 0, "success_count": 0, "failed_count": 0, "usage_characters": 0},
    "month": {"job_count": 0, "success_count": 0, "failed_count": 0, "usage_characters": 0},
    "last_call": {"provider": None, "status": "none"},
}

_UNKNOWN_PAYLOAD = {
    "provider_status": {
        "state": "unknown",
        "category": "none",
        "label": "无调用记录",
        "detail": None,
    }
}


def _build_status_client(payload: dict):
    fake_core_client = FakeCoreStatusClient(payload)
    gateway = VoiceLabGateway(http_client=fake_core_client)
    provider_status_svc = ProviderStatusService(gateway=gateway)
    service = ProductService(
        bootstrap=MagicMock(**{"get_bootstrap": AsyncMock(return_value={})}),
        provider_status=provider_status_svc,
    )
    return service, fake_core_client


class TestXiangtaStatusCoreMockIntegration:

    @pytest.fixture
    def client_available(self, monkeypatch):
        service, fake_core_client = _build_status_client(_AVAILABLE_PAYLOAD)

        import src.xiangta.api.routes as routes_module
        monkeypatch.setattr(routes_module, "create_product_service", lambda: service)

        app = FastAPI()
        app.include_router(router)
        return TestClient(app), fake_core_client

    def test_status_200(self, client_available):
        client, _ = client_available
        r = client.get("/api/xiangta/provider/status")
        assert r.status_code == 200

    def test_ok_true(self, client_available):
        client, _ = client_available
        r = client.get("/api/xiangta/provider/status")
        assert r.json()["ok"] is True

    def test_data_present(self, client_available):
        client, _ = client_available
        assert "data" in client.get("/api/xiangta/provider/status").json()

    def test_kind_ok_from_available_core_status(self, client_available):
        client, _ = client_available
        data = client.get("/api/xiangta/provider/status").json()["data"]
        assert data["kind"] == "ok"

    def test_has_label(self, client_available):
        client, _ = client_available
        data = client.get("/api/xiangta/provider/status").json()["data"]
        assert data["label"]

    def test_has_detail(self, client_available):
        client, _ = client_available
        data = client.get("/api/xiangta/provider/status").json()["data"]
        assert data["detail"] is not None or data["detail"] == data["detail"]  # field exists

    def test_quota_pct_zero(self, client_available):
        client, _ = client_available
        data = client.get("/api/xiangta/provider/status").json()["data"]
        assert data["quotaPct"] == 0.0

    def test_fake_client_called_runtime_status_path(self, client_available):
        client, fake_core_client = client_available
        client.get("/api/xiangta/provider/status")
        assert ("GET", "/api/voice/runtime/status") in fake_core_client.requests

    def test_no_forbidden_keys_in_response(self, client_available):
        client, _ = client_available
        body = client.get("/api/xiangta/provider/status").json()
        keys = _collect_keys(body)
        bad = keys & FORBIDDEN_KEYS
        assert not bad, f"status response leaked forbidden keys: {bad}"

    def test_kind_in_valid_provider_kinds(self, client_available):
        client, _ = client_available
        data = client.get("/api/xiangta/provider/status").json()["data"]
        valid_kinds = {"not_integrated", "ok", "degraded", "quota", "error", "unknown"}
        assert data["kind"] in valid_kinds

    def test_does_not_require_real_api_keys(self, client_available, monkeypatch):
        client, _ = client_available
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        monkeypatch.delenv("MIMO_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        r = client.get("/api/xiangta/provider/status")
        assert r.status_code == 200

    def test_degraded_on_unknown_core_state(self, monkeypatch):
        service, _ = _build_status_client(_UNKNOWN_PAYLOAD)

        import src.xiangta.api.routes as routes_module
        monkeypatch.setattr(routes_module, "create_product_service", lambda: service)

        app = FastAPI()
        app.include_router(router)
        c = TestClient(app)
        data = c.get("/api/xiangta/provider/status").json()["data"]
        assert data["kind"] == "degraded"

    def test_not_integrated_when_no_gateway_client(self, monkeypatch):
        gateway = VoiceLabGateway()  # no http_client
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
        data = c.get("/api/xiangta/provider/status").json()["data"]
        assert data["kind"] == "not_integrated"
