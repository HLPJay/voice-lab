from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_session
from app.core.errors import VoiceLabError, request_validation_error_handler, voice_lab_error_handler


def _make_clean_app(temp_db):
    """Creates a minimal app with an empty temp DB (no seed)."""
    engine, _ = temp_db

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(VoiceLabError, voice_lab_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)

    def override_get_session():
        with Session(engine) as sess:
            yield sess

    app.dependency_overrides[get_session] = override_get_session

    from app.api import api_router
    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": "Voice Lab"}

    return app


def test_render_with_mock_provider(test_app):
    """Full render flow with mock provider."""
    client = TestClient(test_app)
    response = client.post(
        "/api/voice/render",
        json={
            "text": "我一直以为，是生活太难。后来才发现，真正让我害怕的是那个一直在逃避的自己。",
            "profile_id": "deep_night_programmer",
            "provider": "mock",
            "need_subtitle": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"].startswith("job_")
    assert data["status"] == "success"
    assert data["provider"] == "mock"
    assert data["audio_asset"]["id"].startswith("audio_")
    assert data["audio_asset"]["url"]
    assert data["audio_asset"]["duration_ms"] is not None


def test_render_profile_not_found(temp_db):
    """Profile that doesn't exist returns 404."""
    app = _make_clean_app(temp_db)
    client = TestClient(app)
    response = client.post(
        "/api/voice/render",
        json={
            "text": "测试文本",
            "profile_id": "nonexistent_profile",
            "provider": "mock",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROFILE_NOT_FOUND"


def test_render_empty_text(test_app):
    """Empty text returns the unified validation error envelope."""
    client = TestClient(test_app)
    response = client.post(
        "/api/voice/render",
        json={
            "text": "",
            "profile_id": "deep_night_programmer",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed"
