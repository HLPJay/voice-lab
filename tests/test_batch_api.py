import json
import os
import tempfile
from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.database import get_session as _get_session
from app.core.errors import VoiceLabError, request_validation_error_handler, voice_lab_error_handler
from app.core.time import utc_now_iso
from app.models.batch_job import BatchJob, BatchSegment
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile


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

    app.dependency_overrides[_get_session] = override_get_session

    from app.api import api_router
    app.include_router(api_router)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.fixture
def seed_profile_and_binding(session):
    now = utc_now_iso()
    profile = VoiceProfile(
        id="deep_night_programmer",
        name="深夜程序员",
        description="低沉、克制、疲惫但不崩溃，适合深夜独白和情绪 MV。",
        gender_style="male",
        age_style="middle_aged",
        tone_style="low_calm",
        emotion_style="melancholic",
        speed_style="slow",
        pause_style="long",
        scene_tags=["深夜独白", "情绪 MV", "低沉叙事"],
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)

    binding = VoiceBinding(
        id="binding_mock_deep_night_programmer",
        profile_id=profile.id,
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="mock_voice",
        params_json="{}",
        priority=1,
        status="available",
        created_at=now,
        updated_at=now,
    )
    session.add(binding)
    session.commit()
    return binding


def test_submit_longtext_returns_batch_id(
    client: TestClient, session: Session, seed_profile_and_binding
):
    with patch("app.api.batch.service._execute_with_session", return_value=None):
        resp = client.post(
            "/api/voice/batch/submit",
            json={
                "mode": "longtext",
                "text": "第一句。第二句。第三句。",
                "profile_id": "deep_night_programmer",
                "provider": "mock",
                "segment_strategy": "sentence",
                "max_segment_chars": 2000,
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "batch_id" in data
    assert data["batch_id"].startswith("batch_")
    assert data["mode"] == "longtext"
    assert data["total_segments"] >= 1
    assert data["status"] == "pending"


def test_submit_script_returns_batch_id(
    client: TestClient, session: Session, seed_profile_and_binding
):
    with patch("app.api.batch.service._execute_with_session", return_value=None):
        resp = client.post(
            "/api/voice/batch/submit",
            json={
                "mode": "script",
                "script": [
                    {"role": "旁白", "text": "旁白内容。", "profile_id": "deep_night_programmer"},
                    {"role": "角色", "text": "对白内容！", "profile_id": "deep_night_programmer"},
                ],
                "provider": "mock",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "batch_id" in data
    assert data["mode"] == "script"
    assert data["total_segments"] == 2


def test_status_returns_progress(
    client: TestClient, session: Session, seed_profile_and_binding
):
    # Pre-create a batch job and segments in DB
    now = utc_now_iso()
    batch_id = "batch_api_test_001"
    batch_job = BatchJob(
        id=batch_id,
        mode="longtext",
        status="running",
        provider="mock",
        output_format="mp3",
        total_segments=3,
        completed_segments=1,
        failed_segments=1,
        silence_between_ms=0,
        config_json="{}",
        created_at=now,
        updated_at=now,
    )
    session.add(batch_job)

    for i in range(3):
        seg = BatchSegment(
            id=f"batch_api_seg_{i}",
            batch_job_id=batch_id,
            index=i,
            text=f"文本{i}。",
            profile_id="deep_night_programmer",
            params_json="{}",
            status="success" if i < 2 else "pending",
            voice_job_id=f"job_{i}" if i < 2 else None,
            audio_asset_id=f"audio_{i}" if i < 2 else None,
            duration_ms=1000 if i < 2 else None,
            created_at=now,
            updated_at=now,
        )
        session.add(seg)
    session.commit()

    resp = client.get(f"/api/voice/batch/{batch_id}/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["batch_id"] == batch_id
    assert data["total_segments"] == 3
    assert data["completed_segments"] == 1
    assert data["failed_segments"] == 1
    assert data["status"] == "running"
    assert len(data["segments"]) == 3


def test_download_after_complete(
    client: TestClient, session: Session, seed_profile_and_binding
):
    # Pre-create a completed batch with a real merged audio file
    import tempfile
    from pathlib import Path
    from app.utils.audio import write_silent_wav

    now = utc_now_iso()

    # Create a real temporary audio file to serve as the merged audio
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "merged.wav"
        write_silent_wav(audio_path, duration_ms=500)

        # Copy to a persistent location that the app can read
        from app.core.config import get_settings
        settings = get_settings()
        from app.utils.files import storage_path
        persistent_path = storage_path("audio", "batch_api_test_merged.wav")
        import shutil
        shutil.copy(audio_path, persistent_path)

        batch_id = "batch_api_test_002"
        from app.models.voice_asset import AudioAsset
        audio_asset = AudioAsset(
            id="audio_batch_api_001",
            job_id=batch_id,
            provider="mock",
            file_path=str(persistent_path),
            file_url=f"/api/voice/assets/audio_batch_api_001/download",
            format="wav",
            duration_ms=500,
            created_at=now,
        )
        session.add(audio_asset)

        batch_job = BatchJob(
            id=batch_id,
            mode="longtext",
            status="success",
            provider="mock",
            output_format="wav",
            total_segments=1,
            completed_segments=1,
            failed_segments=0,
            merged_audio_asset_id=audio_asset.id,
            silence_between_ms=0,
            config_json="{}",
            created_at=now,
            updated_at=now,
        )
        session.add(batch_job)
        session.commit()

        resp = client.get(f"/api/voice/batch/{batch_id}/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] in ("audio/wav", "audio/x-wav")


def test_submit_empty_text_rejected(client: TestClient, session: Session, seed_profile_and_binding):
    resp = client.post(
        "/api/voice/batch/submit",
        json={
            "mode": "longtext",
            "text": "",
            "profile_id": "deep_night_programmer",
            "provider": "mock",
        },
    )
    assert resp.status_code == 422  # Validation error


def test_submit_script_empty_lines_rejected(client: TestClient, session: Session, seed_profile_and_binding):
    resp = client.post(
        "/api/voice/batch/submit",
        json={
            "mode": "script",
            "script": [
                {"role": "旁白", "text": "", "profile_id": "deep_night_programmer"},
            ],
            "provider": "mock",
        },
    )
    assert resp.status_code == 422  # Validation error
