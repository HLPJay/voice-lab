import pytest
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.database import get_session
from app.core.errors import voice_lab_error_handler, VoiceLabError
from app.core.time import utc_now_iso
from app.models.voice_job import VoiceJob


@pytest.fixture
def test_app(temp_db):
    engine, _ = temp_db

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)
    app.add_exception_handler(VoiceLabError, voice_lab_error_handler)

    from app.api.voice_jobs import router as voice_jobs_router
    app.include_router(voice_jobs_router, prefix="/api/voice")

    def override_get_session():
        with Session(engine) as sess:
            yield sess

    app.dependency_overrides[get_session] = override_get_session
    yield app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


def test_list_jobs_empty(client: TestClient, session: Session):
    response = client.get("/api/voice/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["jobs"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_list_jobs_returns_jobs(client: TestClient, session: Session):
    now = utc_now_iso()
    job = VoiceJob(
        id="job_test_001",
        job_type="tts",
        status="pending",
        provider="minimax",
        model="speech-02",
        profile_id="test_profile",
        input_text="hello",
        processed_text=None,
        provider_trace_id=None,
        error_message=None,
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()

    response = client.get("/api/voice/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["job_id"] == "job_test_001"
    assert data["jobs"][0]["job_type"] == "tts"


def test_list_jobs_filter_by_type(client: TestClient, session: Session):
    now = utc_now_iso()
    job1 = VoiceJob(
        id="job_tts_001",
        job_type="tts",
        status="pending",
        provider="minimax",
        model="speech-02",
        profile_id="test_profile",
        input_text="hello",
        created_at=now,
        updated_at=now,
    )
    job2 = VoiceJob(
        id="job_srt_001",
        job_type="srt",
        status="pending",
        provider="minimax",
        model="speech-02",
        profile_id="test_profile",
        input_text="hello",
        created_at=now,
        updated_at=now,
    )
    session.add_all([job1, job2])
    session.commit()

    response = client.get("/api/voice/jobs?job_type=tts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["job_type"] == "tts"

    response2 = client.get("/api/voice/jobs?job_type=srt")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["total"] == 1
    assert data2["jobs"][0]["job_type"] == "srt"


def test_list_jobs_pagination(client: TestClient, session: Session):
    now = utc_now_iso()
    for i in range(5):
        job = VoiceJob(
            id=f"job_page_{i:03d}",
            job_type="tts",
            status="pending",
            provider="minimax",
            model="speech-02",
            profile_id="test_profile",
            input_text=f"text_{i}",
            created_at=now,
            updated_at=now,
        )
        session.add(job)
    session.commit()

    response = client.get("/api/voice/jobs?limit=2&offset=0")
    data = response.json()
    assert data["total"] == 5
    assert len(data["jobs"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0

    response2 = client.get("/api/voice/jobs?limit=2&offset=2")
    data2 = response2.json()
    assert len(data2["jobs"]) == 2
    assert data2["offset"] == 2

    response3 = client.get("/api/voice/jobs?limit=2&offset=4")
    data3 = response3.json()
    assert len(data3["jobs"]) == 1
    assert data3["offset"] == 4