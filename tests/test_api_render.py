from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_session
from app.core.errors import VoiceLabError, request_validation_error_handler, voice_lab_error_handler
from app.core.time import utc_now_iso
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile
from app.models.provider_voice import ProviderVoice


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


def test_render_with_mock_provider(test_app, seed_mock_binding):
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


def _seed_profile_with_bindings(session, bindings_spec):
    """Helper: create a profile and N bindings from a list of (priority, status, voice_id) tuples.

    Also creates a ProviderVoice record for each binding so that validate_binding_provider_voice passes.
    """
    now = utc_now_iso()
    profile = VoiceProfile(
        id="test_binding_profile",
        name="Test Profile",
        description="For binding selection tests",
        gender_style="male",
        age_style="young",
        tone_style="neutral",
        emotion_style="neutral",
        speed_style="normal",
        pause_style="normal",
        scene_tags_json="[]",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)
    created_bindings = []
    for i, (priority, status, voice_id) in enumerate(bindings_spec):
        b = VoiceBinding(
            id=f"binding_test_{i}",
            profile_id=profile.id,
            provider="mock",
            model="speech-2.8-hd",
            provider_voice_id=voice_id,
            params_json='{"speed":1.0}',
            priority=priority,
            status=status,
            created_at=now,
            updated_at=now,
        )
        session.add(b)

        pv = ProviderVoice(
            id=f"pv_{voice_id}",
            provider="mock",
            provider_voice_id=voice_id,
            voice_type="voice_cloning",
            name=f"Mock Voice {voice_id}",
            status="available",
            created_at=now,
            updated_at=now,
        )
        session.add(pv)
        created_bindings.append(b)
    session.commit()
    return profile, created_bindings


def _make_app_with_session(engine):
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
    return app


def test_render_unsupported_provider(test_app):
    """Unsupported provider returns UNSUPPORTED_PROVIDER, not BINDING_NOT_FOUND."""
    client = TestClient(test_app)
    resp = client.post("/api/voice/render", json={
        "text": "测试",
        "profile_id": "deep_night_programmer",
        "provider": "openai",
    })
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "UNSUPPORTED_PROVIDER"


def test_render_all_bindings_deprecated(temp_db):
    """T1: All bindings deprecated -> BINDING_NOT_FOUND."""
    engine, _ = temp_db
    with Session(engine) as sess:
        _seed_profile_with_bindings(sess, [
            (1, "deprecated", "voice_a"),
            (2, "deprecated", "voice_b"),
        ])
    app = _make_app_with_session(engine)
    client = TestClient(app)
    resp = client.post("/api/voice/render", json={
        "text": "测试",
        "profile_id": "test_binding_profile",
        "provider": "mock",
    })
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "BINDING_NOT_FOUND"


def test_render_selects_highest_priority_binding(temp_db):
    """T2: Multiple available bindings -> select lowest priority number."""
    engine, _ = temp_db
    with Session(engine) as sess:
        _seed_profile_with_bindings(sess, [
            (5, "available", "voice_low_pri"),
            (1, "available", "voice_high_pri"),
        ])
    app = _make_app_with_session(engine)
    client = TestClient(app)
    resp = client.post("/api/voice/render", json={
        "text": "测试",
        "profile_id": "test_binding_profile",
        "provider": "mock",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["model"] == "speech-2.8-hd"


def test_render_ignores_deprecated_binding(temp_db):
    """T3: Mix of deprecated + available -> only available is used."""
    engine, _ = temp_db
    with Session(engine) as sess:
        _seed_profile_with_bindings(sess, [
            (1, "deprecated", "voice_deprecated"),
            (2, "available", "voice_active"),
        ])
    app = _make_app_with_session(engine)
    client = TestClient(app)
    resp = client.post("/api/voice/render", json={
        "text": "测试",
        "profile_id": "test_binding_profile",
        "provider": "mock",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
