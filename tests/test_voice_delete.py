from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlmodel import Session, SQLModel, create_engine

from app.core.database import get_session as _get_session
from app.core.errors import VoiceLabError, request_validation_error_handler, voice_lab_error_handler
from app.core.time import utc_now_iso
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile
from app.models.provider_voice import ProviderVoice


@pytest.fixture
def temp_db():
    import os, tempfile
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
    """FastAPI app sharing the same temp DB as session fixture."""
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
def seed_profile_and_mock_binding(session):
    """Seed a profile + mock binding for delete tests."""
    now = utc_now_iso()
    profile = VoiceProfile(
        id="delete_test_profile",
        name="Delete Test Profile",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(profile)

    binding = VoiceBinding(
        id="binding_mock_delete_test",
        profile_id="delete_test_profile",
        provider="mock",
        model="speech-2.8-hd",
        provider_voice_id="mock_voice_for_delete",
        params_json="{}",
        priority=1,
        status="available",
        created_at=now,
        updated_at=now,
    )
    session.add(binding)
    session.commit()
    return profile, binding


class TestDeleteVoiceLocalState:
    """Verify delete_voice properly updates local provider_voices and bindings."""

    def test_delete_cloning_marks_provider_voice_deprecated(self, test_app, session, seed_profile_and_mock_binding):
        """删除 voice_cloning 成功后，provider_voice.status 变为 deprecated。"""
        from fastapi.testclient import TestClient
        from app.repositories.provider_voice_repo import upsert_provider_voice

        # 先创建一个本地的 voice_cloning provider_voice
        pv = upsert_provider_voice(
            session,
            provider="mock",
            provider_voice_id="mock_clone_soft",
            voice_type="voice_cloning",
            name="Mock Clone Soft",
            status="available",
        )
        session.commit()

        resp = TestClient(test_app).post(
            "/api/voice/voices/delete",
            json={"provider_voice_id": "mock_clone_soft", "voice_type": "voice_cloning"},
            params={"provider": "mock"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["voice_id"] == "mock_clone_soft"
        assert data["deleted"] is True
        assert data["local_provider_voice_updated"] is True

        # 验证数据库状态
        session.expire_all()
        from app.repositories.provider_voice_repo import get_provider_voice
        pv_updated = get_provider_voice(session, provider="mock", provider_voice_id="mock_clone_soft")
        assert pv_updated is not None
        assert pv_updated.status == "deprecated"

    def test_delete_generation_marks_provider_voice_deprecated(self, test_app, session):
        """删除 voice_generation 成功后，provider_voice.status 变为 deprecated。"""
        from fastapi.testclient import TestClient
        from app.repositories.provider_voice_repo import upsert_provider_voice

        upsert_provider_voice(
            session,
            provider="mock",
            provider_voice_id="mock_generated_warm",
            voice_type="voice_generation",
            name="Mock Generated Warm",
            status="available",
        )
        session.commit()

        resp = TestClient(test_app).post(
            "/api/voice/voices/delete",
            json={"provider_voice_id": "mock_generated_warm", "voice_type": "voice_generation"},
            params={"provider": "mock"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] is True
        assert data["local_provider_voice_updated"] is True

        session.expire_all()
        from app.repositories.provider_voice_repo import get_provider_voice
        pv_updated = get_provider_voice(session, provider="mock", provider_voice_id="mock_generated_warm")
        assert pv_updated is not None
        assert pv_updated.status == "deprecated"

    def test_delete_marks_bindings_deprecated(self, test_app, session, seed_profile_and_mock_binding):
        """删除成功后，引用该 provider_voice_id 的 available binding 变为 deprecated。"""
        from fastapi.testclient import TestClient
        from app.repositories.provider_voice_repo import upsert_provider_voice
        from app.repositories.voice_binding_repo import list_bindings

        # 创建本地 provider_voice 和 binding
        upsert_provider_voice(
            session,
            provider="mock",
            provider_voice_id="mock_bindable_voice",
            voice_type="voice_cloning",
            name="Mock Bindable Voice",
            status="available",
        )

        # 该 voice 已经有一个 binding（在 seed_profile_and_mock_binding 里）
        from app.repositories.voice_binding_repo import create_binding
        binding = create_binding(
            session,
            profile_id="delete_test_profile",
            provider="mock",
            model="speech-2.8-hd",
            provider_voice_id="mock_bindable_voice",
            params={},
            priority=1,
        )
        session.commit()
        binding_id = binding.id

        resp = TestClient(test_app).post(
            "/api/voice/voices/delete",
            json={"provider_voice_id": "mock_bindable_voice", "voice_type": "voice_cloning"},
            params={"provider": "mock"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] is True
        assert data["affected_bindings_count"] >= 1

        # binding 应变为 deprecated
        session.expire_all()
        bindings = list_bindings(session, profile_id="delete_test_profile", include_deprecated=True)
        deprecated = [b for b in bindings if b.id == binding_id]
        assert len(deprecated) == 1
        assert deprecated[0].status == "deprecated"

    def test_delete_local_not_found_remote_success(self, test_app, session):
        """本地 provider_voice 不存在但远端删除成功时，接口返回 deleted=true，local_provider_voice_updated=false。"""
        from fastapi.testclient import TestClient

        resp = TestClient(test_app).post(
            "/api/voice/voices/delete",
            json={"provider_voice_id": "nonexistent_remote_voice", "voice_type": "voice_cloning"},
            params={"provider": "mock"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["voice_id"] == "nonexistent_remote_voice"
        assert data["deleted"] is True
        assert data["local_provider_voice_updated"] is False
        assert data["affected_bindings_count"] == 0

    def test_delete_remote_fails_does_not_update_local(self, test_app, session):
        """远端删除失败时，本地 provider_voice 和 bindings 不应被修改。"""
        from fastapi.testclient import TestClient
        from app.repositories.provider_voice_repo import upsert_provider_voice

        upsert_provider_voice(
            session,
            provider="mock",
            provider_voice_id="mock_always_fail",
            voice_type="voice_cloning",
            name="Mock Always Fail",
            status="available",
        )
        session.commit()

        # 模拟远端删除失败
        class FailingAdapter:
            provider_name = "mock"
            async def delete_voice(self, provider_voice_id, voice_type):
                from app.core.errors import ProviderError
                raise ProviderError("Remote delete failed", "voice not found on provider")

        with patch("app.services.voice_delete_service.get_provider", return_value=FailingAdapter()):
            resp = TestClient(test_app).post(
                "/api/voice/voices/delete",
                json={"provider_voice_id": "mock_always_fail", "voice_type": "voice_cloning"},
                params={"provider": "mock"},
            )

        assert resp.status_code == 400

        # 本地状态不应变化
        session.expire_all()
        from app.repositories.provider_voice_repo import get_provider_voice
        pv = get_provider_voice(session, provider="mock", provider_voice_id="mock_always_fail")
        assert pv is not None
        assert pv.status == "available"


class TestDeleteSystemVoiceRejected:
    def test_delete_system_voice_rejected(self, test_app):
        """voice_type=system 被 422 拒绝。"""
        from fastapi.testclient import TestClient

        resp = TestClient(test_app).post(
            "/api/voice/voices/delete",
            json={"provider_voice_id": "some_voice", "voice_type": "system"},
            params={"provider": "mock"},
        )
        assert resp.status_code == 422

    def test_delete_empty_voice_id_rejected(self, test_app):
        """空 voice_id 被 422 拒绝。"""
        from fastapi.testclient import TestClient

        resp = TestClient(test_app).post(
            "/api/voice/voices/delete",
            json={"provider_voice_id": "", "voice_type": "voice_cloning"},
            params={"provider": "mock"},
        )
        assert resp.status_code == 422
