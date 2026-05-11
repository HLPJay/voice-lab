import os
import tempfile
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlmodel import Session, SQLModel, create_engine

from app.api import api_router
from app.core.database import get_session
from app.core.errors import VoiceLabError, request_validation_error_handler, voice_lab_error_handler
from app.core.time import utc_now_iso
from app.models.provider_voice import ProviderVoice
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile
from app.repositories.provider_voice_repo import upsert_provider_voice


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine, path
    engine.dispose()
    os.unlink(path)


@pytest.fixture
def session(temp_db):
    engine, _ = temp_db
    with Session(engine) as sess:
        yield sess


@pytest.fixture
def test_app(temp_db, session):
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

    from app.core.database import get_session as _get_session
    app.dependency_overrides[_get_session] = override_get_session
    app.include_router(api_router)
    return app


@pytest.fixture
def seed_data(session):
    now = utc_now_iso()
    profile = VoiceProfile(
        id="test_profile",
        name="Test Profile",
        description="A test profile",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)

    pv1 = upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="Voice_Alpha",
        voice_type="system",
        name="Voice Alpha",
        status="available",
    )
    pv2 = upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="Voice_Beta",
        voice_type="system",
        name="Voice Beta",
        status="available",
    )
    session.commit()
    return {"profile": profile, "pv1": pv1, "pv2": pv2}


@pytest.fixture
def client(test_app):
    from fastapi.testclient import TestClient
    return TestClient(test_app)


class TestListBindings:
    def test_get_list_empty(self, client, seed_data):
        resp = client.get("/api/voice/profiles/test_profile/bindings")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_list_returns_bindings(self, client, session, seed_data):
        now = utc_now_iso()
        binding = VoiceBinding(
            id="b1",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json='{"speed": 0.9}',
            priority=1,
            status="available",
            created_at=now,
            updated_at=now,
        )
        session.add(binding)
        session.commit()

        resp = client.get("/api/voice/profiles/test_profile/bindings")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == "b1"
        assert data[0]["provider_voice_name"] == "Voice Alpha"

    def test_get_profile_not_found(self, client, seed_data):
        resp = client.get("/api/voice/profiles/nonexistent_profile/bindings")
        assert resp.status_code == 404


class TestCreateBinding:
    def test_post_create_valid(self, client, seed_data):
        resp = client.post(
            "/api/voice/profiles/test_profile/bindings",
            json={
                "provider": "minimax",
                "model": "speech-2.8-hd",
                "provider_voice_id": "Voice_Alpha",
                "params": {"speed": 0.88},
                "priority": 1,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["profile_id"] == "test_profile"
        assert data["provider"] == "minimax"
        assert data["provider_voice_id"] == "Voice_Alpha"
        assert data["params"] == {"speed": 0.88}
        assert data["status"] == "available"

    def test_post_duplicate_returns_422(self, client, seed_data):
        client.post(
            "/api/voice/profiles/test_profile/bindings",
            json={"provider": "minimax", "model": "speech-2.8-hd", "provider_voice_id": "Voice_Alpha"},
        )
        resp = client.post(
            "/api/voice/profiles/test_profile/bindings",
            json={"provider": "minimax", "model": "speech-2.8-hd", "provider_voice_id": "Voice_Alpha"},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "Duplicate binding" in resp.json()["error"]["message"]

    def test_post_missing_profile_returns_404(self, client, seed_data):
        resp = client.post(
            "/api/voice/profiles/nonexistent_profile/bindings",
            json={"provider": "minimax", "model": "speech-2.8-hd", "provider_voice_id": "Voice_Alpha"},
        )
        assert resp.status_code == 404
        assert resp.json().get("error", {}).get("code") == "PROFILE_NOT_FOUND", f"got: {resp.json()}"

    def test_post_missing_provider_voice_returns_422(self, client, seed_data):
        resp = client.post(
            "/api/voice/profiles/test_profile/bindings",
            json={"provider": "minimax", "model": "speech-2.8-hd", "provider_voice_id": "NonExistent"},
        )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "not found or not available" in resp.json()["error"]["message"]


class TestUpdateBinding:
    def test_patch_update_params_priority(self, client, session, seed_data):
        now = utc_now_iso()
        binding = VoiceBinding(
            id="b_patch_test",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json='{"speed": 0.9}',
            priority=1,
            status="available",
            created_at=now,
            updated_at=now,
        )
        session.add(binding)
        session.commit()

        resp = client.patch(
            "/api/voice/bindings/b_patch_test",
            json={"params": {"speed": 0.95}, "priority": 3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["params"] == {"speed": 0.95}
        assert data["priority"] == 3

    def test_patch_duplicate_provider_voice_id_returns_422(self, client, session, seed_data):
        now = utc_now_iso()
        b1 = VoiceBinding(
            id="b_dup_1",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json="{}",
            priority=1,
            status="available",
            created_at=now,
            updated_at=now,
        )
        b2 = VoiceBinding(
            id="b_dup_2",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Beta",
            params_json="{}",
            priority=2,
            status="available",
            created_at=now,
            updated_at=now,
        )
        session.add(b1)
        session.add(b2)
        session.commit()

        resp = client.patch(
            "/api/voice/bindings/b_dup_1",
            json={"provider_voice_id": "Voice_Beta"},
        )
        assert resp.status_code == 422
        assert "Duplicate binding" in resp.json()["error"]["message"]

    def test_patch_not_found_returns_404(self, client, seed_data):
        resp = client.patch("/api/voice/bindings/nonexistent", json={"priority": 5})
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "BINDING_NOT_FOUND"


class TestDeleteBinding:
    def test_delete_deprecates_binding(self, client, session, seed_data):
        now = utc_now_iso()
        binding = VoiceBinding(
            id="b_delete_test",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json="{}",
            priority=1,
            status="available",
            created_at=now,
            updated_at=now,
        )
        session.add(binding)
        session.commit()

        resp = client.delete("/api/voice/bindings/b_delete_test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "deprecated"

        raw = session.get(VoiceBinding, "b_delete_test")
        assert raw.status == "deprecated"
        assert raw.provider_voice_id == "Voice_Alpha"

    def test_delete_not_found_returns_404(self, client, seed_data):
        resp = client.delete("/api/voice/bindings/nonexistent")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "BINDING_NOT_FOUND"
