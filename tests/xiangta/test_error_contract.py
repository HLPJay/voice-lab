"""
Tests for minimal flat error response contract (trimmed to 6 tests).

Covers:
1. error_body() returns complete flat shape
2. error_response() returns status_code and flat body (no detail)
3. Admin disabled returns 403 flat shape, no detail
4. Admin wrong token returns 403, no token leak
5. Suggestions ValueError returns flat shape, no detail
6. TTS mapping error returns flat shape, no detail
"""
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.error_contract import error_body, error_response
from src.xiangta.api.routes import router


def _create_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_error_body_returns_complete_flat_shape():
    """error_body returns all four fields: ok, errorKind, message, retryable."""
    body = error_body(error_kind="test_kind", message="test message")
    assert body["ok"] is False
    assert body["errorKind"] == "test_kind"
    assert body["message"] == "test message"
    assert body["retryable"] is False


def test_error_response_returns_status_code_and_flat_body():
    """error_response returns specified status_code with flat body (no detail)."""
    resp = error_response(status_code=404, error_kind="not_found", message="not found")
    assert resp.status_code == 404
    data = json.loads(resp.body)
    assert data["ok"] is False
    assert data["errorKind"] == "not_found"
    assert data["message"] == "not found"
    assert data["retryable"] is False
    assert "detail" not in data


def test_admin_disabled_returns_403_flat_shape_no_detail(monkeypatch):
    """Admin disabled returns 403 with flat shape, no detail wrapper."""
    monkeypatch.delenv("XIANGTA_ADMIN_ENABLED", raising=False)
    monkeypatch.delenv("XIANGTA_ADMIN_TOKEN", raising=False)

    response = _create_client().get("/api/xiangta/admin/config")

    assert response.status_code == 403
    data = response.json()
    assert "detail" not in data
    assert data["ok"] is False
    assert data["errorKind"] == "admin_forbidden"
    assert data["retryable"] is False


def test_admin_wrong_token_returns_403_no_token_leak(monkeypatch):
    """Admin wrong token returns 403 and does not leak real token in response."""
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")
    monkeypatch.setenv("XIANGTA_ADMIN_TOKEN", "expected-token")

    response = _create_client().get(
        "/api/xiangta/admin/config",
        headers={"X-XiangTa-Admin-Token": "wrong-token"},
    )

    assert response.status_code == 403
    assert "expected-token" not in response.text
    assert "wrong-token" not in response.text
    data = response.json()
    assert "detail" not in data
    assert data["ok"] is False
    assert data["errorKind"] == "admin_forbidden"


def test_suggestions_value_error_returns_flat_shape_no_detail(monkeypatch):
    """When service raises ValueError, suggestions returns flat 400 shape (no detail)."""
    from src.xiangta.services.product_service import ProductService

    async def fake_get_suggestions(self, *args, **kwargs):
        raise ValueError("recipient not configured for this scene")

    monkeypatch.setattr(ProductService, "get_suggestions", fake_get_suggestions)

    response = _create_client().post(
        "/api/xiangta/suggestions",
        json={"recipient": "lover", "scene": "miss", "rawText": "我想说一些话"},
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" not in data
    assert data["ok"] is False
    assert data["errorKind"] == "invalid_input"
    assert data["retryable"] is False


def test_tts_mapping_error_returns_flat_shape_no_detail(monkeypatch):
    """When voice preset mapping fails, TTS returns flat 400 shape (no detail)."""
    from src.xiangta.services import voice_preset_mapping_service as service_module
    from src.xiangta.services.voice_preset_mapping_service import VoicePresetDisabled

    def broken_resolve(self, *args, **kwargs):
        raise VoicePresetDisabled("voicePreset 'male-mature' 已禁用")

    monkeypatch.setattr(service_module.VoicePresetMappingService, "resolve", broken_resolve)

    response = _create_client().post(
        "/api/xiangta/tts",
        json={
            "text": "hello",
            "voicePreset": "male-mature",
            "tone": "gentle",
            "recipient": "lover",
            "scene": "miss",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" not in data
    assert data["ok"] is False
    assert "errorKind" in data
    assert data["retryable"] is False