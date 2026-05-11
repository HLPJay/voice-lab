from sqlmodel import Session

from app.models.voice_variant import VoiceVariant, VoiceVariantGroup


def create_group(session: Session, group: VoiceVariantGroup) -> VoiceVariantGroup:
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def create_variant(session: Session, variant: VoiceVariant) -> VoiceVariant:
    session.add(variant)
    session.commit()
    session.refresh(variant)
    return variant
