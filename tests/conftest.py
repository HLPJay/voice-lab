import os
import tempfile
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlmodel import Session, SQLModel, create_engine

from app.core.errors import VoiceLabError, request_validation_error_handler, voice_lab_error_handler
from app.core.middleware import RequestContextMiddleware
from app.core.time import utc_now_iso
from app.models.provider_voice import ProviderVoice
from app.models.voice_binding import VoiceBinding
from app.models.voice_job import VoiceJob
from app.models.voice_profile import VoiceProfile
from app.models.voice_variant import VoiceVariant, VoiceVariantGroup
from app.models.voice_asset import AudioAsset, SubtitleAsset


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: end-to-end tests requiring real MiniMax API key")


@pytest.fixture(autouse=True)
def clean_logging_setup():
    """Ensure root logger has a default handler at INFO level for all tests.

    This fixture runs after each test that has autouse=True (e.g. test_logging.py's
    reset_logging). It restores the root logger to a usable state so that
    modules that don't call setup_logging() (e.g. test_middleware.py) still
    have a stream handler at INFO level.
    """
    import sys
    import logging
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # Ensure stdout handler exists
    has_handler = any(isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr) for h in root.handlers)
    if not has_handler:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
        root.addHandler(h)
    yield
    # No teardown — let each module manage its own state


@pytest.fixture(autouse=True)
def reset_httpx_shared_client():
    """Reset the shared httpx client and settings cache before each test to ensure test isolation."""
    import app.providers.minimax_speech_adapter as adapter_module
    from app.core.config import clear_settings_cache
    adapter_module._shared_http_client = None
    clear_settings_cache()
    yield


def pytest_collection_modifyitems(config, items):
    if config.getoption("-m", default=None) == "e2e":
        return
    skip_e2e = pytest.mark.skip(reason="run with -m e2e to execute E2E tests")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


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
def seed_profile(session):
    now = utc_now_iso()
    profile = VoiceProfile(
        id="deep_night_programmer",
        name="深夜程序员",
        description="低沉、克制、疲惫但不崩溃，适合深夜独白和情绪 MV。",
        gender_style="male",
        age_style="middle_aged",
        tone_style="low_calm",
        emotion_style="sad_calm",
        speed_style="slow",
        pause_style="slow_reflective",
        scene_tags_json='["deep_night_monologue","emotional_mv"]',
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    binding = VoiceBinding(
        id="binding_minimax_deep_night_programmer",
        profile_id=profile.id,
        provider="minimax",
        model="speech-2.8-hd",
        provider_voice_id="English_expressive_narrator",
        params_json='{"speed":0.88,"vol":1,"pitch":0,"emotion":"sad"}',
        priority=1,
        status="available",
        created_at=now,
        updated_at=now,
    )
    session.add(profile)
    session.add(binding)
    session.commit()
    return profile, binding


@pytest.fixture
def seed_mock_binding(session, seed_profile):
    """Add a mock provider binding for the seeded profile."""
    profile, _ = seed_profile
    now = utc_now_iso()
    binding = VoiceBinding(
        id="binding_mock_deep_night_programmer",
        profile_id=profile.id,
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="mock_voice",
        params_json='{}',
        priority=1,
        status="available",
        created_at=now,
        updated_at=now,
    )
    session.add(binding)
    session.commit()
    return binding


@pytest.fixture
def ws_patched_session(session):
    """Patch ws_render.get_session to use the test session's engine.

    The WS endpoint calls `next(get_session())` directly, bypassing FastAPI's
    dependency_overrides. We patch the ws_render module's reference so the
    WS endpoint uses the same engine as the test session.
    """
    from app.api import ws_render
    from sqlmodel import Session

    # Use the SAME engine that the test's session uses
    engine = session.bind.engine

    def patched_get_session():
        with Session(engine) as sess:
            yield sess

    original = ws_render.get_session
    ws_render.get_session = patched_get_session
    yield
    ws_render.get_session = original


@pytest.fixture
def test_app(temp_db, seed_profile):
    """Minimal FastAPI app that uses the same temp DB as seed_profile."""
    engine, _ = temp_db

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(VoiceLabError, voice_lab_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)

    def override_get_session():
        with Session(engine) as sess:
            yield sess

    from app.core.database import get_session
    app.dependency_overrides[get_session] = override_get_session

    from app.api import api_router
    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": "Voice Lab"}

    return app


@pytest.fixture
def e2e_app(temp_db, seed_profile):
    """FastAPI app using real provider settings from .env (no DB override for providers)."""
    engine, _ = temp_db

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(VoiceLabError, voice_lab_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)

    def override_get_session():
        with Session(engine) as sess:
            yield sess

    from app.core.database import get_session
    app.dependency_overrides[get_session] = override_get_session

    from app.api import api_router
    app.include_router(api_router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "app": "Voice Lab"}

    return app


@pytest.fixture
def minimax_api_key():
    """Skip if no real API key configured."""
    from app.core.config import get_settings
    settings = get_settings()
    key = settings.minimax_api_key
    if not key or key == "replace_me":
        pytest.skip("MINIMAX_API_KEY not configured")
    return key
