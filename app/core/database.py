from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import get_settings
from app.core.time import utc_now_iso
from app.domain.enums import BindingStatus
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile
from app.models.voice_asset import AudioAsset, SubtitleAsset
from app.models.voice_job import VoiceJob
from app.models.voice_variant import VoiceVariant, VoiceVariantGroup
from app.models.provider_voice import ProviderVoice
from app.models.provider_call_log import ProviderCallLog  # noqa: F401
from app.models.batch_job import BatchJob, BatchSegment  # noqa: F401


engine = create_engine(get_settings().database_url, connect_args={"check_same_thread": False})


def get_engine():
    return engine


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def seed_defaults() -> None:
    with Session(engine) as session:
        exists = session.exec(select(VoiceProfile).limit(1)).first()
        if exists:
            return
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
            scene_tags_json='["deep_night_monologue","emotional_mv","programmer_reflection"]',
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        binding = VoiceBinding(
            id="binding_minimax_deep_night_programmer",
            profile_id=profile.id,
            provider="minimax",
            model=get_settings().minimax_default_model,
            provider_voice_id="English_expressive_narrator",
            params_json='{"speed":0.88,"vol":1,"pitch":0,"emotion":"sad"}',
            priority=1,
            status=BindingStatus.available,
            created_at=now,
            updated_at=now,
        )
        mock_binding = VoiceBinding(
            id="binding_mock_deep_night_programmer",
            profile_id=profile.id,
            provider="mock",
            model="mock-tts",
            provider_voice_id="mock_voice_default",
            params_json='{"speed":0.88,"emotion":"neutral"}',
            priority=1,
            status=BindingStatus.available,
            created_at=now,
            updated_at=now,
        )
        session.add(profile)
        session.add(binding)
        session.add(mock_binding)
        session.commit()
