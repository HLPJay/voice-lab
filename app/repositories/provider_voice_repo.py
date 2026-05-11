import json

from sqlmodel import Session, select

from app.core.time import utc_now_iso
from app.domain.enums import ProviderVoiceStatus
from app.models.provider_voice import ProviderVoice
from app.utils.id_generator import new_id


def list_provider_voices(
    session: Session,
    *,
    provider: str,
    voice_type: str = "all",
    include_deprecated: bool = False,
) -> list[ProviderVoice]:
    stmt = select(ProviderVoice).where(ProviderVoice.provider == provider)
    if voice_type != "all":
        stmt = stmt.where(ProviderVoice.voice_type == voice_type)
    if not include_deprecated:
        stmt = stmt.where(ProviderVoice.status == ProviderVoiceStatus.available)
    stmt = stmt.order_by(ProviderVoice.voice_type, ProviderVoice.name)
    return list(session.exec(stmt).all())


def get_provider_voice(session: Session, *, provider: str, provider_voice_id: str) -> ProviderVoice | None:
    stmt = (
        select(ProviderVoice)
        .where(ProviderVoice.provider == provider)
        .where(ProviderVoice.provider_voice_id == provider_voice_id)
    )
    return session.exec(stmt).first()


def upsert_provider_voice(
    session: Session,
    *,
    provider: str,
    provider_voice_id: str,
    voice_type: str,
    name: str | None = None,
    description: str | None = None,
    language: str | None = None,
    gender: str | None = None,
    status: str = ProviderVoiceStatus.available,
    provider_created_time: str | None = None,
    metadata: dict | None = None,
    synced_at: str | None = None,
) -> ProviderVoice:
    now = utc_now_iso()
    item = get_provider_voice(session, provider=provider, provider_voice_id=provider_voice_id)
    if item is None:
        item = ProviderVoice(
            id=new_id("pv"),
            provider=provider,
            provider_voice_id=provider_voice_id,
            voice_type=voice_type,
            created_at=now,
            updated_at=now,
        )
    item.voice_type = voice_type
    item.name = name
    item.description = description
    item.language = language
    item.gender = gender
    item.status = status
    item.provider_created_time = provider_created_time
    item.metadata_json = json.dumps(metadata or {}, ensure_ascii=False)
    item.synced_at = synced_at or now
    item.updated_at = now
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def mark_missing_provider_voices_deprecated(
    session: Session,
    *,
    provider: str,
    seen_provider_voice_ids: set[str],
    synced_at: str | None = None,
) -> int:
    now = utc_now_iso()
    mark_time = synced_at or now
    existing = list_provider_voices(session, provider=provider, include_deprecated=False)
    changed = 0
    for item in existing:
        if item.provider_voice_id in seen_provider_voice_ids:
            continue
        item.status = ProviderVoiceStatus.deprecated
        item.synced_at = mark_time
        item.updated_at = now
        session.add(item)
        changed += 1
    if changed:
        session.commit()
    return changed
