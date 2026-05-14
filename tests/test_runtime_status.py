"""Tests for GET /api/voice/runtime/status"""

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
from app.models.provider_call_log import ProviderCallLog
from app.models.voice_asset import AudioAsset
from app.models.voice_job import VoiceJob


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
def test_app(temp_db):
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


class TestRuntimeStatusEmpty:
    """Empty database returns zero stats."""

    def test_returns_200_empty_db(self, test_app):
        from fastapi.testclient import TestClient
        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200

    def test_today_month_zero_empty_db(self, test_app):
        from fastapi.testclient import TestClient
        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["today"]["job_count"] == 0
        assert data["today"]["success_count"] == 0
        assert data["today"]["failed_count"] == 0
        assert data["today"]["usage_characters"] == 0
        assert data["month"]["job_count"] == 0
        assert data["month"]["success_count"] == 0
        assert data["month"]["failed_count"] == 0
        assert data["month"]["usage_characters"] == 0

    def test_last_call_none_empty_db(self, test_app):
        from fastapi.testclient import TestClient
        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["last_call"]["status"] == "none"
        assert data["provider_status"]["state"] == "unknown"
        assert data["provider_status"]["label"] == "无调用记录"

    def test_current_fields_present(self, test_app):
        from fastapi.testclient import TestClient
        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "default_provider" in data["current"]
        assert "default_model" in data["current"]
        assert "default_ws_model" in data["current"]
        assert "default_audio_format" in data["current"]


class TestVoiceJobStats:
    """VoiceJob counts are reflected in today/month stats."""

    def test_today_job_count(self, test_app, session):
        from fastapi.testclient import TestClient
        now = utc_now_iso()
        for i in range(3):
            job = VoiceJob(
                id=f"job_{i}",
                job_type="sync_render",
                status="success",
                provider="mock",
                model="speech-02-hd",
                created_at=now,
                updated_at=now,
            )
            session.add(job)
        session.commit()

        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        assert resp.json()["today"]["job_count"] == 3
        assert resp.json()["today"]["success_count"] == 3
        assert resp.json()["today"]["failed_count"] == 0

    def test_failed_job_count(self, test_app, session):
        from fastapi.testclient import TestClient
        now = utc_now_iso()
        for i in range(2):
            job = VoiceJob(
                id=f"fail_job_{i}",
                job_type="sync_render",
                status="failed",
                provider="mock",
                model="speech-02-hd",
                created_at=now,
                updated_at=now,
            )
            session.add(job)
        session.commit()

        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        assert resp.json()["today"]["failed_count"] == 2


class TestUsageCharacters:
    """usage_characters is max of ProviderCallLog and AudioAsset, avoiding double-count."""

    def test_provider_call_log_usage(self, test_app, session):
        from fastapi.testclient import TestClient
        now = utc_now_iso()
        log = ProviderCallLog(
            id="log1",
            provider="minimax",
            api_path="/v1/t2a_v2",
            method="POST",
            usage_characters=500,
            created_at=now,
        )
        session.add(log)
        session.commit()

        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        assert resp.json()["today"]["usage_characters"] == 500

    def test_audio_asset_usage(self, test_app, session):
        from fastapi.testclient import TestClient
        now = utc_now_iso()
        asset = AudioAsset(
            id="asset1",
            job_id="job1",
            provider="minimax",
            file_path="audio/test.mp3",
            usage_characters=800,
            created_at=now,
        )
        session.add(asset)
        session.commit()

        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        assert resp.json()["today"]["usage_characters"] == 800

    def test_usage_characters_max_not_sum(self, test_app, session):
        """When both have values, use max (not sum) to avoid double-counting."""
        from fastapi.testclient import TestClient
        now = utc_now_iso()
        log = ProviderCallLog(
            id="log_max",
            provider="minimax",
            api_path="/v1/t2a_v2",
            method="POST",
            usage_characters=300,
            created_at=now,
        )
        asset = AudioAsset(
            id="asset_max",
            job_id="job_max",
            provider="minimax",
            file_path="audio/test2.mp3",
            usage_characters=500,
            created_at=now,
        )
        session.add(log)
        session.add(asset)
        session.commit()

        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        # Should be max(300, 500) = 500, not 300 + 500 = 800
        assert resp.json()["today"]["usage_characters"] == 500


class TestLastCall:
    """Last call state reflected correctly."""

    def test_last_call_success(self, test_app, session):
        from fastapi.testclient import TestClient
        now = utc_now_iso()
        log = ProviderCallLog(
            id="log_ok",
            provider="minimax",
            api_path="/v1/t2a_v2",
            method="POST",
            status_code=200,
            usage_characters=100,
            created_at=now,
        )
        session.add(log)
        session.commit()

        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["last_call"]["status"] == "success"
        assert data["last_call"]["provider"] == "minimax"
        assert data["provider_status"]["state"] == "available"
        assert data["provider_status"]["label"] == "正常"

    def test_last_call_error(self, test_app, session):
        from fastapi.testclient import TestClient
        now = utc_now_iso()
        log = ProviderCallLog(
            id="log_err",
            provider="minimax",
            api_path="/v1/t2a_v2",
            method="POST",
            status_code=500,
            error_type="MiniMaxError",
            error_message="Internal server error",
            created_at=now,
        )
        session.add(log)
        session.commit()

        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["last_call"]["status"] == "error"
        assert data["last_call"]["error_type"] == "MiniMaxError"
        assert data["provider_status"]["state"] == "error"
        assert data["provider_status"]["label"] == "最近调用异常"


class TestReadOnly:
    """Interface is read-only — no side effects."""

    def test_no_external_provider_calls(self, test_app):
        """Does not call external Provider even without real API key."""
        from fastapi.testclient import TestClient
        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        # Would be 200 even without network — just reads local DB
        assert resp.status_code == 200

    def test_no_job_modification(self, test_app, session):
        """Does not create or modify any VoiceJob records."""
        from fastapi.testclient import TestClient
        from sqlalchemy import text
        before = session.exec(text("SELECT count(*) FROM voice_jobs")).one()
        client = TestClient(test_app)
        resp = client.get("/api/voice/runtime/status")
        assert resp.status_code == 200
        after = session.exec(text("SELECT count(*) FROM voice_jobs")).one()
        assert before == after
