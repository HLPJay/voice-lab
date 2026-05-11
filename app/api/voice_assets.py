from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.core.database import get_session
from app.core.errors import AssetNotFound
from app.repositories import voice_asset_repo

router = APIRouter()


def _asset_not_found(asset_id: str) -> None:
    raise AssetNotFound("Asset not found", detail=asset_id)


@router.get("/assets/{asset_id}")
async def get_asset(
    asset_id: str,
    session: Session = Depends(get_session),
):
    audio = voice_asset_repo.get_audio_asset(session, asset_id)
    if audio:
        return {
            "asset_id": audio.id,
            "type": "audio",
            "file_path": audio.file_path,
            "format": audio.format,
            "duration_ms": audio.duration_ms,
            "provider": audio.provider,
            "model": audio.model,
            "usage_characters": audio.usage_characters,
            "download_url": audio.file_url,
            "created_at": audio.created_at,
        }
    subtitle = voice_asset_repo.get_subtitle_asset(session, asset_id)
    if subtitle:
        return {
            "asset_id": subtitle.id,
            "type": "subtitle",
            "file_path": subtitle.file_path,
            "srt_path": subtitle.srt_path,
            "subtitle_type": subtitle.subtitle_type,
            "timeline": subtitle.timeline_json,
            "created_at": subtitle.created_at,
        }
    _asset_not_found(asset_id)


@router.get("/assets/{asset_id}/download")
async def download_asset(
    asset_id: str,
    session: Session = Depends(get_session),
):
    audio = voice_asset_repo.get_audio_asset(session, asset_id)
    if audio:
        path = Path(audio.file_path)
        if not path.exists():
            _asset_not_found(asset_id)
        return FileResponse(
            path,
            media_type="audio/wav" if audio.format == "wav" else "audio/mpeg",
            filename=f"{asset_id}.{audio.format}",
        )
    subtitle = voice_asset_repo.get_subtitle_asset(session, asset_id)
    if subtitle:
        srt_path = subtitle.srt_path
        path = Path(srt_path) if srt_path else None
        if not path or not path.exists():
            json_path = Path(subtitle.file_path)
            if not json_path.exists():
                _asset_not_found(asset_id)
            path = json_path
        return FileResponse(
            path,
            media_type="application/json" if path.suffix == ".json" else "text/srt",
            filename=f"{asset_id}{path.suffix}",
        )
    _asset_not_found(asset_id)
