from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.core.errors import JobNotFound
from app.domain.schemas import AudioAssetResponse, SubtitleAssetResponse, VoiceJobDeleteResponse, VoiceJobRead
from app.repositories import voice_asset_repo, voice_job_repo

router = APIRouter()


def _audio_asset_response(asset) -> AudioAssetResponse | None:
    if not asset:
        return None
    return AudioAssetResponse(
        id=asset.id,
        url=asset.file_url,
        duration_ms=asset.duration_ms,
        format=asset.format,
    )


def _subtitle_asset_response(asset) -> SubtitleAssetResponse | None:
    if not asset:
        return None
    return SubtitleAssetResponse(
        id=asset.id,
        url=f"/api/voice/assets/{asset.id}/download",
        timeline=[],
    )


def _job_read_with_assets(session: Session, job) -> VoiceJobRead:
    audio_asset = voice_asset_repo.get_latest_audio_asset_for_job(session, job.id)
    subtitle_asset = voice_asset_repo.get_latest_subtitle_asset_for_job(session, job.id)
    return VoiceJobRead(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        provider=job.provider,
        model=job.model,
        profile_id=job.profile_id,
        input_text=job.input_text,
        processed_text=job.processed_text,
        provider_trace_id=job.provider_trace_id,
        error_message=job.error_message,
        audio_asset=_audio_asset_response(audio_asset),
        subtitle_asset=_subtitle_asset_response(subtitle_asset),
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/jobs")
async def list_jobs(
    job_type: str | None = None,
    status: str | None = None,
    profile_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
):
    jobs, total = voice_job_repo.list_jobs(
        session,
        job_type=job_type,
        status=status,
        profile_id=profile_id,
        limit=limit,
        offset=offset,
    )
    return {
        "jobs": [_job_read_with_assets(session, job) for job in jobs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/jobs/{job_id}", response_model=VoiceJobRead)
async def get_job(
    job_id: str,
    session: Session = Depends(get_session),
):
    job = voice_job_repo.get_job(session, job_id)
    if not job or job.status == "deleted":
        raise JobNotFound("Voice job not found", job_id=job_id)
    return _job_read_with_assets(session, job)


@router.delete("/jobs/{job_id}", response_model=VoiceJobDeleteResponse)
async def delete_job(
    job_id: str,
    session: Session = Depends(get_session),
):
    job = voice_job_repo.get_job(session, job_id)
    if not job:
        raise JobNotFound("Voice job not found", job_id=job_id)

    if job.status == "deleted":
        return VoiceJobDeleteResponse(
            job_id=job.id,
            deleted=True,
            status="deleted",
            message="历史任务已删除",
        )

    job = voice_job_repo.soft_delete_job(session, job)
    return VoiceJobDeleteResponse(
        job_id=job.id,
        deleted=True,
        status=job.status,
        message="历史任务已删除",
    )
