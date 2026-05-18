from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.xiangta.api.routes import router


def _create_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_admin_config_returns_403_by_default(monkeypatch):
    monkeypatch.delenv("XIANGTA_ADMIN_ENABLED", raising=False)
    monkeypatch.delenv("XIANGTA_ADMIN_TOKEN", raising=False)

    response = _create_client().get("/api/xiangta/admin/config")

    assert response.status_code == 403


def test_admin_config_returns_403_when_enabled_without_token(monkeypatch):
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")
    monkeypatch.delenv("XIANGTA_ADMIN_TOKEN", raising=False)

    response = _create_client().get("/api/xiangta/admin/config")

    assert response.status_code == 403


def test_admin_config_returns_403_when_token_is_invalid(monkeypatch):
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")
    monkeypatch.setenv("XIANGTA_ADMIN_TOKEN", "expected-token")

    response = _create_client().get(
        "/api/xiangta/admin/config",
        headers={"X-XiangTa-Admin-Token": "wrong-token"},
    )

    assert response.status_code == 403
    assert "expected-token" not in response.text
    assert "wrong-token" not in response.text


def test_admin_config_returns_200_when_token_matches(monkeypatch):
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")
    monkeypatch.setenv("XIANGTA_ADMIN_TOKEN", "test-admin-token")

    response = _create_client().get(
        "/api/xiangta/admin/config",
        headers={"X-XiangTa-Admin-Token": "test-admin-token"},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert "test-admin-token" not in response.text


def test_public_voice_presets_does_not_require_admin_token(monkeypatch):
    monkeypatch.delenv("XIANGTA_ADMIN_ENABLED", raising=False)
    monkeypatch.delenv("XIANGTA_ADMIN_TOKEN", raising=False)

    response = _create_client().get("/api/xiangta/voice-presets")

    assert response.status_code == 200
    assert response.json()["ok"] is True
