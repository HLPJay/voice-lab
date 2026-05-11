from sqlmodel import Session, select

from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile


def list_profiles(session: Session) -> list[VoiceProfile]:
    return list(session.exec(select(VoiceProfile).where(VoiceProfile.is_active == True)).all())


def get_profile(session: Session, profile_id: str) -> VoiceProfile | None:
    return session.get(VoiceProfile, profile_id)


def get_binding(session: Session, profile_id: str, provider: str) -> VoiceBinding | None:
    stmt = (
        select(VoiceBinding)
        .where(VoiceBinding.profile_id == profile_id)
        .where(VoiceBinding.provider == provider)
        .where(VoiceBinding.status == "available")
        .order_by(VoiceBinding.priority, VoiceBinding.created_at)
    )
    return session.exec(stmt).first()
