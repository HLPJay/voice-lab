import json
import tempfile
from pathlib import Path

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


def test_admin_api_works_with_local_json_token(monkeypatch, tmp_path):
    """Admin API accepts token from configs/xiangta.runtime.local.json admin.token."""
    import src.xiangta.config.runtime_config as rc_module

    monkeypatch.delenv("XIANGTA_ADMIN_TOKEN", raising=False)
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")

    local_path = tmp_path / "xiangta.runtime.local.json"
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump({
            "admin": {
                "enabled": True,
                "token": "local-json-token",
            },
        }, f)
    monkeypatch.setattr(rc_module, "_RUNTIME_LOCAL_JSON_PATH", local_path)

    response = _create_client().get(
        "/api/xiangta/admin/config",
        headers={"X-XiangTa-Admin-Token": "local-json-token"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_admin_api_wrong_token_still_403_with_local_json(monkeypatch, tmp_path):
    """Wrong token still returns 403 even when local json has a valid token."""
    import src.xiangta.config.runtime_config as rc_module

    monkeypatch.delenv("XIANGTA_ADMIN_TOKEN", raising=False)
    monkeypatch.setenv("XIANGTA_ADMIN_ENABLED", "true")

    local_path = tmp_path / "xiangta.runtime.local.json"
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump({
            "admin": {
                "enabled": True,
                "token": "correct-local-token",
            },
        }, f)
    monkeypatch.setattr(rc_module, "_RUNTIME_LOCAL_JSON_PATH", local_path)

    response = _create_client().get(
        "/api/xiangta/admin/config",
        headers={"X-XiangTa-Admin-Token": "wrong-token"},
    )
    assert response.status_code == 403
    assert "correct-local-token" not in response.text
