from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.errors import BindingNotFound, ProfileNotFound
from app.core.time import utc_now_iso
from app.domain.enums import BindingStatus
from app.models.voice_binding import VoiceBinding
from app.models.voice_profile import VoiceProfile


def list_profiles(session: Session) -> list[VoiceProfile]:
    return list(session.exec(select(VoiceProfile).where(VoiceProfile.is_active == True)).all())


def get_profile(session: Session, profile_id: str) -> VoiceProfile | None:
    return session.get(VoiceProfile, profile_id)


def archive_profile(session: Session, profile: VoiceProfile) -> VoiceProfile:
    profile.is_active = False
    profile.updated_at = utc_now_iso()
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def get_binding(session: Session, profile_id: str, provider: str) -> VoiceBinding | None:
    stmt = (
        select(VoiceBinding)
        .where(VoiceBinding.profile_id == profile_id)
        .where(VoiceBinding.provider == provider)
        .where(VoiceBinding.status == BindingStatus.available)
        .order_by(VoiceBinding.priority, VoiceBinding.created_at)
    )
    return session.exec(stmt).first()


def resolve_binding(session: Session, profile_id: str, provider: str) -> tuple[VoiceBinding, str]:
    """Resolve a binding for a profile+provider, with mock-fallback support.

    Returns (binding, resolved_provider). Raises ProfileNotFound or BindingNotFound.
    """
    profile = get_profile(session, profile_id)
    if not profile:
        raise ProfileNotFound("Voice profile not found", profile_id)
    if not profile.is_active:
        raise ProfileNotFound(
            "该人设已归档，不能用于新生成",
            f"PROFILE_ARCHIVED:{profile_id}",
        )

    binding = get_binding(session, profile_id, provider)
    if binding:
        return binding, provider

    settings = get_settings()
    if provider == "mock" and settings.mock_fallback_provider:
        binding = get_binding(session, profile_id, settings.mock_fallback_provider)
        if binding:
            return binding, settings.mock_fallback_provider

    raise BindingNotFound(
        "No available voice binding found",
        f"profile={profile_id}, provider={provider}",
    )
