"""
Tests for minimal flat error response contract.

Covers:
1. error_body() returns ok=false/errorKind/message/retryable
2. error_response() returns specified status_code
3. Admin disabled returns 403
4. Admin disabled response is flat shape, no detail
5. Admin wrong token returns 403, response doesn't contain real token
6. Suggestions invalid input returns flat shape, no detail
7. TTS invalid/unconfigured preset returns flat shape, no detail
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.error_contract import error_body, error_response
from src.xiangta.api.routes import router


def _create_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestErrorBody:
    def test_returns_ok_false(self):
        body = error_body(error_kind="test_kind", message="test message")
        assert body["ok"] is False

    def test_returns_error_kind(self):
        body = error_body(error_kind="test_kind", message="test message")
        assert body["errorKind"] == "test_kind"

    def test_returns_message(self):
        body = error_body(error_kind="test_kind", message="test message")
        assert body["message"] == "test message"

    def test_returns_retryable_default_false(self):
        body = error_body(error_kind="test_kind", message="test message")
        assert body["retryable"] is False

    def test_returns_retryable_true(self):
        body = error_body(error_kind="test_kind", message="test message", retryable=True)
        assert body["retryable"] is True


class TestErrorResponse:
    def test_returns_specified_status_code(self):
        resp = error_response(status_code=404, error_kind="not_found", message="not found")
        assert resp.status_code == 404

    def test_body_has_flat_shape(self):
        resp = error_response(status_code=400, error_kind="invalid_input", message="bad input")
        body = resp.body
        import json
        data = json.loads(body)
        assert "ok" in data
        assert "errorKind" in data
        assert "message" in data
        assert "retryable" in data
        assert "detail" not in data


class TestAdminGateFlatError:
    def test_admin_disabled_returns_403(self, monkeypatch):
        monkeypatch.delenv("XIANGTA_ADMIN_ENABLED", raising=False)
        monkeypatch.delenv("XIANGTA_ADMIN_TOKEN", raising=False)

        response = _create_client().get("/api/xiangta/admin/config")

        assert response.status_code == 403

    def test_admin_disabled_response_is_flat_no_detail(self, monkeypatch):
        monkeypatch.delenv("XIANGTA_ADMIN_ENABLED", raising=False)
        monkeypatch.delenv("XIANGTA_ADMIN_TOKEN", raising=False)

        response = _create_client().get("/api/xiangta/admin/config")

        data = response.json()
        assert "detail" not in data
        assert data["ok"] is False
        assert data["errorKind"] == "admin_forbidden"
        assert "message" in data
        assert data["retryable"] is False

    def test_admin_wrong_token_returns_403_no_token_leak(self, monkeypatch):
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


class TestSuggestionsFlatError:
    def test_service_raises_value_error_returns_flat_shape_no_detail(self, monkeypatch):
        """When service raises ValueError, suggestions handler returns flat 400 shape."""
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
        assert "message" in data
        assert data["retryable"] is False


class TestTtsFlatError:
    def test_disabled_preset_returns_flat_shape_no_detail(self, monkeypatch):
        """When voice preset is disabled, TTS returns flat 400 shape (not detail wrapper)."""
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
        assert "message" in data
        assert "retryable" in data