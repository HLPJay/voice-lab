import os
import tempfile
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlmodel import Session, SQLModel, create_engine

from app.api import api_router
from app.core.errors import ProfileNotFound, ValidationError, request_validation_error_handler, voice_lab_error_handler, VoiceLabError
from app.core.time import utc_now_iso
from app.domain.enums import BindingStatus, JobStatus, JobType
from app.domain.schemas import VoiceProfileCreate
from app.models.voice_asset import AudioAsset
from app.models.voice_binding import VoiceBinding
from app.models.voice_job import VoiceJob
from app.models.voice_profile import VoiceProfile
from app.repositories.voice_profile_repo import get_profile, resolve_binding
from app.services.voice_profile_service import VoiceProfileService


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
def client(temp_db):
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

    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture
def seed_profile_data(session):
    now = utc_now_iso()
    active_profile = VoiceProfile(
        id="archive_profile_active",
        name="Archive Active",
        description="active profile",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    inactive_profile = VoiceProfile(
        id="archive_profile_inactive",
        name="Archive Inactive",
        description="inactive profile",
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    binding = VoiceBinding(
        id="binding_archive_keep",
        profile_id=active_profile.id,
        provider="minimax",
        model="speech-2.8-hd",
        provider_voice_id="Voice_Archive",
        params_json="{}",
        priority=1,
        status=BindingStatus.available,
        created_at=now,
        updated_at=now,
    )
    job = VoiceJob(
        id="job_archive_keep",
        job_type=JobType.sync_render,
        status=JobStatus.success,
        provider="minimax",
        model="speech-2.8-hd",
        profile_id=active_profile.id,
        binding_id=binding.id,
        input_text="hello",
        processed_text="hello",
        render_plan_json="{}",
        created_at=now,
        updated_at=now,
    )
    asset = AudioAsset(
        id="audio_archive_keep",
        job_id=job.id,
        provider="minimax",
        model="speech-2.8-hd",
        file_path="audio/archive_keep.wav",
        file_url="/api/voice/assets/audio_archive_keep/download",
        format="wav",
        duration_ms=1000,
        created_at=now,
    )
    session.add(active_profile)
    session.add(inactive_profile)
    session.add(binding)
    session.add(job)
    session.add(asset)
    session.commit()
    return {
        "active_profile_id": active_profile.id,
        "inactive_profile_id": inactive_profile.id,
        "binding_id": binding.id,
        "job_id": job.id,
        "asset_id": asset.id,
    }


class TestVoiceProfileArchiveApi:
    def test_archive_active_profile_success(self, client, session, seed_profile_data):
        resp = client.patch("/api/voice/profiles/archive_profile_active/archive")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "archive_profile_active"
        assert data["is_active"] is False

        raw = get_profile(session, "archive_profile_active")
        assert raw is not None
        assert raw.is_active is False

    def test_archive_inactive_profile_is_idempotent(self, client, session, seed_profile_data):
        resp = client.patch("/api/voice/profiles/archive_profile_inactive/archive")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "archive_profile_inactive"
        assert data["is_active"] is False

        raw = get_profile(session, "archive_profile_inactive")
        assert raw is not None
        assert raw.is_active is False

    def test_archive_nonexistent_profile_returns_404(self, client, seed_profile_data):
        resp = client.patch("/api/voice/profiles/nonexistent_profile/archive")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "PROFILE_NOT_FOUND"

    def test_list_profiles_excludes_archived_by_default(self, client, seed_profile_data):
        resp = client.get("/api/voice/profiles")
        assert resp.status_code == 200
        ids = [item["id"] for item in resp.json()]
        assert "archive_profile_active" in ids
        assert "archive_profile_inactive" not in ids


class TestArchivedProfileLifecycle:
    def test_archived_profile_cannot_resolve_binding(self, session, seed_profile_data):
        profile = get_profile(session, "archive_profile_active")
        profile.is_active = False
        profile.updated_at = utc_now_iso()
        session.add(profile)
        session.commit()

        with pytest.raises(ProfileNotFound) as exc_info:
            resolve_binding(session, "archive_profile_active", "minimax")

        assert exc_info.value.detail == "PROFILE_ARCHIVED:archive_profile_active"
        assert "归档" in exc_info.value.message

    def test_archive_does_not_delete_binding(self, client, session, seed_profile_data):
        resp = client.patch("/api/voice/profiles/archive_profile_active/archive")
        assert resp.status_code == 200

        binding = session.get(VoiceBinding, seed_profile_data["binding_id"])
        assert binding is not None
        assert binding.status == BindingStatus.available

    def test_archive_does_not_delete_job_or_audio_asset(self, client, session, seed_profile_data):
        resp = client.patch("/api/voice/profiles/archive_profile_active/archive")
        assert resp.status_code == 200

        job = session.get(VoiceJob, seed_profile_data["job_id"])
        asset = session.get(AudioAsset, seed_profile_data["asset_id"])
        assert job is not None
        assert asset is not None
        assert job.profile_id == "archive_profile_active"
        assert asset.job_id == "job_archive_keep"

    def test_create_does_not_silently_revive_archived_profile(self, session, seed_profile_data):
        service = VoiceProfileService()

        with pytest.raises(ValidationError) as exc_info:
            service.create(
                session,
                VoiceProfileCreate(id="archive_profile_inactive", name="Revive Attempt"),
            )

        assert "不能通过创建接口恢复" in exc_info.value.message

        profile = get_profile(session, "archive_profile_inactive")
        assert profile is not None
        assert profile.is_active is False
