import json
from pathlib import Path

from sqlmodel import Session

from app.core.logging import get_logger
from app.core.time import utc_now_iso
from app.models.voice_asset import AudioAsset, SubtitleAsset
from app.repositories import voice_asset_repo
from app.providers.base import ProviderRenderResult
from app.utils.files import storage_path
from app.utils.id_generator import new_id
from app.utils.srt import timeline_to_srt

_logger = get_logger("asset_service")


def _valid_duration_ms(value) -> int | None:
    """Coerce a duration value to a positive int, or return None if invalid."""
    try:
        if value is None:
            return None
        n = int(value)
        return n if n > 0 else None
    except (TypeError, ValueError):
        return None


def _probe_audio_duration_ms(audio_path: Path) -> int | None:
    """Read real audio duration from a local audio file using pydub.

    Returns None if the file doesn't exist or cannot be parsed.
    Does not raise — failures are silent.
    """
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(str(audio_path))
        duration_ms = len(audio)
        return duration_ms if duration_ms > 0 else None
    except Exception:
        return None


class AssetService:
    def save_assets(
        self,
        session: Session,
        *,
        job_id: str,
        provider: str,
        model: str,
        result: ProviderRenderResult,
        audio_params: dict,
        subtitle_type: str,
    ) -> tuple[AudioAsset, SubtitleAsset | None]:
        now = utc_now_iso()
        audio_id = new_id("audio")
        audio_path = Path(result.audio_path)

        duration_ms = _valid_duration_ms(result.duration_ms)
        if duration_ms is None:
            duration_ms = _probe_audio_duration_ms(audio_path)

        audio_asset = AudioAsset(
            id=audio_id,
            job_id=job_id,
            provider=provider,
            model=model,
            file_path=str(audio_path),
            file_url=f"/api/voice/assets/{audio_id}/download",
            format=audio_path.suffix.lstrip(".") or audio_params.get("format"),
            duration_ms=duration_ms,
            sample_rate=audio_params.get("sample_rate"),
            bitrate=audio_params.get("bitrate"),
            channel=audio_params.get("channel"),
            usage_characters=result.usage_characters,
            metadata_json=json.dumps(result.metadata, ensure_ascii=False),
            created_at=now,
        )
        subtitle_asset = None
        if result.timeline:
            subtitle_id = new_id("subtitle")
            subtitle_json_path = storage_path("subtitles", f"{subtitle_id}.json")
            subtitle_srt_path = storage_path("subtitles", f"{subtitle_id}.srt")
            subtitle_json_path.write_text(json.dumps(result.timeline, ensure_ascii=False, indent=2), encoding="utf-8")
            subtitle_srt_path.write_text(timeline_to_srt(result.timeline), encoding="utf-8")
            subtitle_asset = SubtitleAsset(
                id=subtitle_id,
                job_id=job_id,
                audio_asset_id=audio_id,
                subtitle_type=subtitle_type,
                file_path=str(subtitle_json_path),
                srt_path=str(subtitle_srt_path),
                timeline_json=json.dumps(result.timeline, ensure_ascii=False),
                created_at=now,
            )
        audio_asset = voice_asset_repo.create_audio_asset(session, audio_asset)
        if subtitle_asset:
            subtitle_asset = voice_asset_repo.create_subtitle_asset(session, subtitle_asset)
        return audio_asset, subtitle_asset
