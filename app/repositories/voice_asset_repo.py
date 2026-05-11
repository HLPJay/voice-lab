from sqlmodel import Session

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
