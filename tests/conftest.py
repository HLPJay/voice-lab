import os
import tempfile

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.core.database import get_session
from app.core.time import utc_now_iso
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile
from app.models.voice_asset import AudioAsset, SubtitleAsset
from app.models.voice_job import VoiceJob
from app.models.voice_variant import VoiceVariant, VoiceVariantGroup


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine, path
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
