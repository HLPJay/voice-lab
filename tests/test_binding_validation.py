"""Tests for binding_validation_service — guards render paths against deleted/deprecated provider voices."""

import os
import tempfile
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.core.database import get_session as _get_session
from app.core.errors import VoiceLabError, request_validation_error_handler, voice_lab_error_handler
from app.core.time import utc_now_iso
from app.domain.enums import ProviderVoiceStatus
from app.models.provider_voice import ProviderVoice
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile
from app.providers.base import ProviderRenderResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
def profile_and_mock_binding(session):
    """Profile + mock binding whose provider_voice exists in DB and is available."""
    now = utc_now_iso()
    profile = VoiceProfile(
        id="bv_profile",
        name="BV Profile",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)

    binding = VoiceBinding(
        id="bv_binding",
        profile_id="bv_profile",
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="mock_available_voice",
        params_json="{}",
        priority=1,
        status="available",
        created_at=now,
        updated_at=now,
    )
    session.add(binding)

    pv = ProviderVoice(
        id="pv_mock_available",
        provider="mock",
        provider_voice_id="mock_available_voice",
        voice_type="voice_cloning",
        name="Mock Available Voice",
        status=ProviderVoiceStatus.available,
        created_at=now,
        updated_at=now,
    )
    session.add(pv)
    session.commit()
    return profile, binding, pv


# ---------------------------------------------------------------------------
# T2A / sync render tests
# ---------------------------------------------------------------------------

class TestSyncRenderBindingValidation:
    """validate_binding_provider_voice guard in voice_render_service.render_voice."""

    def test_available_voice_renders_successfully(self, test_app, session, profile_and_mock_binding):
        """Available provider_voice → render succeeds with 200."""
        profile, binding, pv = profile_and_mock_binding
        client = TestClient(test_app)
        resp = client.post(
            "/api/voice/render",
            json={
                "text": "Hello world",
                "profile_id": "bv_profile",
                "provider": "mock",
            },
        )
        # Real mock adapter handles the render; we just verify success
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["audio_asset"]["id"].startswith("audio_")

    def test_deprecated_voice_rejected_before_render(self, test_app, session, profile_and_mock_binding):
        """Deprecated provider_voice → 422 ValidationError, render_sync NOT called."""
        profile, binding, pv = profile_and_mock_binding

        pv.status = ProviderVoiceStatus.deprecated
        session.add(pv)
        session.commit()

        # Patch get_provider so render_sync is never reached
        mock_adapter = AsyncMock()
        mock_adapter.render_sync = AsyncMock()

        with patch("app.services.voice_render_service.get_provider", return_value=mock_adapter):
            resp = TestClient(test_app).post(
                "/api/voice/render",
                json={
                    "text": "Hello deprecated",
                    "profile_id": "bv_profile",
                    "provider": "mock",
                },
            )

        # ValidationError → 422
        assert resp.status_code == 422
        assert mock_adapter.render_sync.call_count == 0

    def test_missing_provider_voice_rejected_before_render(self, test_app, session, profile_and_mock_binding):
        """provider_voice record deleted → 422 ValidationError, render_sync NOT called."""
        profile, binding, pv = profile_and_mock_binding

        session.delete(pv)
        session.commit()

        mock_adapter = AsyncMock()
        mock_adapter.render_sync = AsyncMock()

        with patch("app.services.voice_render_service.get_provider", return_value=mock_adapter):
            resp = TestClient(test_app).post(
                "/api/voice/render",
                json={
                    "text": "Hello missing",
                    "profile_id": "bv_profile",
                    "provider": "mock",
                },
            )

        assert resp.status_code == 422
        assert mock_adapter.render_sync.call_count == 0


# ---------------------------------------------------------------------------
# Async render tests
# ---------------------------------------------------------------------------

class TestAsyncRenderBindingValidation:
    """validate_binding_provider_voice guard in async_render_service.submit_task."""

    def test_deprecated_voice_no_create_async_task(self, test_app, session, profile_and_mock_binding):
        """Deprecated provider_voice → error before create_async_task is called."""
        profile, binding, pv = profile_and_mock_binding
        pv.status = ProviderVoiceStatus.deprecated
        session.add(pv)
        session.commit()

        mock_adapter = AsyncMock()
        mock_adapter.create_async_task = AsyncMock()

        with patch("app.services.async_render_service.get_provider", return_value=mock_adapter):
            resp = TestClient(test_app).post(
                "/api/voice/render/async",
                json={
                    "text": "Hello async deprecated",
                    "profile_id": "bv_profile",
                    "provider": "mock",
                    "need_subtitle": False,
                },
            )

        # ValidationError → 422
        assert resp.status_code == 422
        assert mock_adapter.create_async_task.call_count == 0


# ---------------------------------------------------------------------------
# Batch render tests
# ---------------------------------------------------------------------------

class TestBatchRenderBindingValidation:
    """validate_binding_provider_voice guard in batch_orchestration_service._process_segment."""

    def test_batch_segment_deprecated_voice_fails_without_render(self, test_app, session, profile_and_mock_binding):
        """Batch segment with deprecated provider_voice → segment failed, render_sync never called."""
        profile, binding, pv = profile_and_mock_binding
        pv.status = ProviderVoiceStatus.deprecated
        session.add(pv)
        session.commit()

        mock_adapter = AsyncMock()
        mock_adapter.render_sync = AsyncMock()

        def patched_get_session():
            from sqlmodel import Session as SqlSession
            engine = session.bind.engine
            yield SqlSession(engine)

        with patch("app.core.database.get_session", patched_get_session):
            with patch("app.services.batch_orchestration_service.get_provider", return_value=mock_adapter):
                resp = TestClient(test_app).post(
                    "/api/voice/batch/submit",
                    json={
                        "mode": "longtext",
                        "text": "Batch deprecated segment",
                        "profile_id": "bv_profile",
                        "provider": "mock",
                        "params": {},
                    },
                )

        assert resp.status_code == 200
        batch_id = resp.json()["batch_id"]

        # Poll status until segment settles (background task runs fast)
        import time
        for _ in range(20):
            status_resp = TestClient(test_app).get(f"/api/voice/batch/{batch_id}/status")
            data = status_resp.json()
            failed = [s for s in data["segments"] if s["status"] == "failed"]
            if failed:
                break
            time.sleep(0.1)

        failed = [s for s in data["segments"] if s["status"] == "failed"]
        assert len(failed) >= 1, f"Expected failed segment, got: {data['segments']}"
        # render_sync on the mock adapter should never have been called
        assert mock_adapter.render_sync.call_count == 0
