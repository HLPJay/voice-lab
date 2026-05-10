import json
import os
import tempfile

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.core.errors import BindingNotFound, ProfileNotFound, ValidationError
from app.core.time import utc_now_iso
from app.domain.schemas import VoiceBindingCreate, VoiceBindingUpdate
from app.models.provider_voice import ProviderVoice
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile
from app.repositories.provider_voice_repo import upsert_provider_voice
from app.services.voice_binding_service import VoiceBindingService


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
    pv_deprecated = upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="Voice_Deprecated",
        voice_type="system",
        name="Voice Deprecated",
        status="deprecated",
    )
    session.commit()
    return {"profile": profile, "pv1": pv1, "pv2": pv2, "pv_deprecated": pv_deprecated}


@pytest.fixture
def service():
    return VoiceBindingService()


@pytest.fixture
def seed_data_two_profiles(session):
    """Two separate profiles sharing the same provider_voice_id."""
    now = utc_now_iso()
    profile_a = VoiceProfile(
        id="profile_a",
        name="Profile A",
        description="First profile",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    profile_b = VoiceProfile(
        id="profile_b",
        name="Profile B",
        description="Second profile",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session.add(profile_a)
    session.add(profile_b)

    pv1 = upsert_provider_voice(
        session,
        provider="minimax",
        provider_voice_id="Shared_Voice",
        voice_type="system",
        name="Shared Voice",
        status="available",
    )
    session.commit()
    return {"profile_a": profile_a, "profile_b": profile_b, "pv1": pv1}


class TestListBindings:
    def test_list_empty(self, session, seed_data, service):
        reads = service.list_profile_bindings(session, "test_profile")
        assert reads == []

    def test_list_returns_all_active(self, session, seed_data, service):
        binding1 = VoiceBinding(
            id="b1",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json='{"speed":0.9}',
            priority=1,
            status="available",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        binding2 = VoiceBinding(
            id="b2",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Beta",
            params_json='{"speed":1.0}',
            priority=2,
            status="available",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(binding1)
        session.add(binding2)
        session.commit()

        reads = service.list_profile_bindings(session, "test_profile")
        assert len(reads) == 2
        ids = {r.id for r in reads}
        assert ids == {"b1", "b2"}

    def test_list_excludes_deprecated(self, session, seed_data, service):
        binding = VoiceBinding(
            id="b_deprecated",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json="{}",
            priority=1,
            status="deprecated",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(binding)
        session.commit()

        reads = service.list_profile_bindings(session, "test_profile")
        assert reads == []

    def test_profile_not_found(self, session, seed_data, service):
        with pytest.raises(ProfileNotFound):
            service.list_profile_bindings(session, "nonexistent_profile")


class TestCreateBinding:
    def test_create_valid(self, session, seed_data, service):
        request = VoiceBindingCreate(
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params={"speed": 0.88, "emotion": "sad"},
            priority=1,
        )
        read = service.create_profile_binding(session, "test_profile", request)

        assert read.profile_id == "test_profile"
        assert read.provider == "minimax"
        assert read.model == "speech-2.8-hd"
        assert read.provider_voice_id == "Voice_Alpha"
        assert read.provider_voice_name == "Voice Alpha"
        assert read.params == {"speed": 0.88, "emotion": "sad"}
        assert read.priority == 1
        assert read.status == "available"

    def test_create_duplicate_fails(self, session, seed_data, service):
        request = VoiceBindingCreate(
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
        )
        service.create_profile_binding(session, "test_profile", request)

        with pytest.raises(ValidationError) as exc_info:
            service.create_profile_binding(session, "test_profile", request)
        assert "Duplicate binding" in str(exc_info.value.message)

    def test_create_with_missing_profile_fails(self, session, seed_data, service):
        request = VoiceBindingCreate(
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
        )
        with pytest.raises(ProfileNotFound):
            service.create_profile_binding(session, "nonexistent_profile", request)

    def test_create_with_missing_provider_voice_fails(self, session, seed_data, service):
        request = VoiceBindingCreate(
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="NonExistent_Voice",
        )
        with pytest.raises(ValidationError) as exc_info:
            service.create_profile_binding(session, "test_profile", request)
        assert "not found or not available" in str(exc_info.value.message)

    def test_create_with_deprecated_provider_voice_fails(self, session, seed_data, service):
        request = VoiceBindingCreate(
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Deprecated",
        )
        with pytest.raises(ValidationError) as exc_info:
            service.create_profile_binding(session, "test_profile", request)
        assert "not found or not available" in str(exc_info.value.message)


class TestUpdateBinding:
    def test_update_params_and_priority(self, session, seed_data, service):
        binding = VoiceBinding(
            id="b_update_test",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json='{"speed":0.9}',
            priority=1,
            status="available",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(binding)
        session.commit()

        request = VoiceBindingUpdate(params={"speed": 0.95}, priority=3)
        read = service.update_binding(session, "b_update_test", request)

        assert read.params == {"speed": 0.95}
        assert read.priority == 3
        assert read.provider_voice_id == "Voice_Alpha"

    def test_update_provider_voice_id_valid(self, session, seed_data, service):
        binding = VoiceBinding(
            id="b_update_voice",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json="{}",
            priority=1,
            status="available",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(binding)
        session.commit()

        request = VoiceBindingUpdate(provider_voice_id="Voice_Beta")
        read = service.update_binding(session, "b_update_voice", request)

        assert read.provider_voice_id == "Voice_Beta"
        assert read.provider_voice_name == "Voice Beta"

    def test_update_provider_voice_id_invalid(self, session, seed_data, service):
        binding = VoiceBinding(
            id="b_update_voice_invalid",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json="{}",
            priority=1,
            status="available",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(binding)
        session.commit()

        request = VoiceBindingUpdate(provider_voice_id="NonExistent_Voice")
        with pytest.raises(ValidationError):
            service.update_binding(session, "b_update_voice_invalid", request)

    def test_update_binding_not_found(self, session, seed_data, service):
        request = VoiceBindingUpdate(priority=5)
        with pytest.raises(BindingNotFound):
            service.update_binding(session, "nonexistent_binding", request)


class TestDeprecateBinding:
    def test_deprecate_keeps_row_status_deprecated(self, session, seed_data, service):
        binding = VoiceBinding(
            id="b_deprecate_test",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json="{}",
            priority=1,
            status="available",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(binding)
        session.commit()

        read = service.deprecate_binding(session, "b_deprecate_test")

        assert read.status == "deprecated"
        assert read.provider_voice_id == "Voice_Alpha"

        raw = session.get(VoiceBinding, "b_deprecate_test")
        assert raw.status == "deprecated"

    def test_deprecate_nonexistent_raises(self, session, seed_data, service):
        with pytest.raises(BindingNotFound):
            service.deprecate_binding(session, "nonexistent_binding")


class TestCrossProfileBinding:
    """Same provider_voice_id can be bound to multiple different profiles with different IDs."""

    def test_same_voice_id_two_profiles_no_id_conflict(self, session, seed_data_two_profiles, service):
        """Creating bindings for the same provider_voice_id on two different profiles must not conflict."""
        request_a = VoiceBindingCreate(
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Shared_Voice",
        )
        read_a = service.create_profile_binding(session, "profile_a", request_a)
        assert read_a.provider_voice_id == "Shared_Voice"
        assert read_a.profile_id == "profile_a"

        request_b = VoiceBindingCreate(
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Shared_Voice",
        )
        read_b = service.create_profile_binding(session, "profile_b", request_b)
        assert read_b.provider_voice_id == "Shared_Voice"
        assert read_b.profile_id == "profile_b"

        assert read_a.id != read_b.id


class TestUpdateDuplicateCheck:
    """update_binding must reject a provider_voice_id change that would create a duplicate."""

    def test_update_provider_voice_id_to_duplicate_raises(self, session, seed_data, service):
        """Changing provider_voice_id to one that already exists on this profile must fail."""
        binding1 = VoiceBinding(
            id="b_dup_1",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json="{}",
            priority=1,
            status="available",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        binding2 = VoiceBinding(
            id="b_dup_2",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Beta",
            params_json="{}",
            priority=2,
            status="available",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(binding1)
        session.add(binding2)
        session.commit()

        request = VoiceBindingUpdate(provider_voice_id="Voice_Beta")
        with pytest.raises(ValidationError) as exc_info:
            service.update_binding(session, "b_dup_1", request)
        assert "Duplicate binding" in str(exc_info.value.message)

    def test_update_provider_voice_id_to_self_is_ok(self, session, seed_data, service):
        """Updating to the same provider_voice_id (no change) must not raise duplicate."""
        binding = VoiceBinding(
            id="b_self",
            profile_id="test_profile",
            provider="minimax",
            model="speech-2.8-hd",
            provider_voice_id="Voice_Alpha",
            params_json='{"speed": 0.9}',
            priority=1,
            status="available",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(binding)
        session.commit()

        request = VoiceBindingUpdate(provider_voice_id="Voice_Alpha", params={"speed": 0.95})
        read = service.update_binding(session, "b_self", request)
        assert read.provider_voice_id == "Voice_Alpha"
        assert read.params == {"speed": 0.95}
