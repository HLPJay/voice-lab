from sqlmodel import Session, select

from app.models.voice_asset import AudioAsset, SubtitleAsset


def get_audio_asset(session: Session, asset_id: str) -> AudioAsset | None:
    return session.get(AudioAsset, asset_id)


def get_subtitle_asset(session: Session, asset_id: str) -> SubtitleAsset | None:
    return session.get(SubtitleAsset, asset_id)


def create_audio_asset(session: Session, asset: AudioAsset) -> AudioAsset:
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def create_subtitle_asset(session: Session, asset: SubtitleAsset) -> SubtitleAsset:
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def get_latest_audio_asset_for_job(session: Session, job_id: str) -> AudioAsset | None:
    statement = (
        select(AudioAsset)
        .where(AudioAsset.job_id == job_id)
        .order_by(AudioAsset.created_at.desc())
    )
    return session.exec(statement).first()


def get_latest_subtitle_asset_for_job(session: Session, job_id: str) -> SubtitleAsset | None:
    statement = (
        select(SubtitleAsset)
        .where(SubtitleAsset.job_id == job_id)
        .order_by(SubtitleAsset.created_at.desc())
    )
    return session.exec(statement).first()
