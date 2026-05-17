import json

from sqlmodel import Session

from app.core.errors import ProfileNotFound, ValidationError
from app.core.time import utc_now_iso
from app.domain.schemas import VoiceProfileCreate, VoiceProfileRead
from app.models.voice_profile import VoiceProfile
from app.repositories.voice_profile_repo import archive_profile, get_profile, list_profiles


def profile_to_read(profile: VoiceProfile) -> VoiceProfileRead:
    return VoiceProfileRead(
        id=profile.id,
        name=profile.name,
        description=profile.description,
        gender_style=profile.gender_style,
        age_style=profile.age_style,
        tone_style=profile.tone_style,
        emotion_style=profile.emotion_style,
        speed_style=profile.speed_style,
        pause_style=profile.pause_style,
        scene_tags=json.loads(profile.scene_tags_json or "[]"),
        is_active=profile.is_active,
    )


class VoiceProfileService:
    def list(self, session: Session) -> list[VoiceProfileRead]:
        return [profile_to_read(item) for item in list_profiles(session)]

    def archive(self, session: Session, profile_id: str) -> VoiceProfileRead:
        profile = get_profile(session, profile_id)
        if not profile:
            raise ProfileNotFound("Voice profile not found", profile_id)
        if profile.is_active:
            profile = archive_profile(session, profile)
        return profile_to_read(profile)

    def create(self, session: Session, request: VoiceProfileCreate) -> VoiceProfileRead:
        existing = get_profile(session, request.id)
        if existing and not existing.is_active:
            raise ValidationError(
                "该人设已归档，不能通过创建接口恢复；如需恢复请使用未来的恢复功能",
                f"PROFILE_ARCHIVED:{request.id}",
            )

        now = utc_now_iso()
        profile = VoiceProfile(
            id=request.id,
            name=request.name,
            description=request.description,
            gender_style=request.gender_style,
            age_style=request.age_style,
            tone_style=request.tone_style,
            emotion_style=request.emotion_style,
            speed_style=request.speed_style,
            pause_style=request.pause_style,
            scene_tags_json=json.dumps(request.scene_tags, ensure_ascii=False),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        if existing:
            profile.created_at = existing.created_at
        session.merge(profile)
        session.commit()
        return profile_to_read(profile)
