from pathlib import Path

from fastapi import APIRouter, Body, Depends
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlmodel import Session

from app.core.database import get_session
from app.core.errors import VoiceLabError
from app.domain.schemas import (
    BatchSubmitResponse,
    BatchStatusResponse,
    LongtextBatchRequest,
    ScriptBatchRequest,
)
from app.repositories import voice_asset_repo
from app.services.batch_orchestration_service import BatchOrchestrationService

router = APIRouter()
service = BatchOrchestrationService()


@router.post("/batch/submit", response_model=BatchSubmitResponse)
async def submit_batch(
    request: LongtextBatchRequest | ScriptBatchRequest = Body(...),
    session: Session = Depends(get_session),
):
    """提交批量任务。根据 mode 字段分发。"""
    try:
        if isinstance(request, LongtextBatchRequest):
            return await service.submit_longtext(session, request)
        else:
            return await service.submit_script(session, request)
    except VoiceLabError:
        raise
    except ValidationError as exc:
        raise VoiceLabError("Invalid request", "VALIDATION_ERROR") from exc


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def batch_status(
    batch_id: str,
    session: Session = Depends(get_session),
):
    """查询批量任务进度。"""
    return await service.get_status(session, batch_id)


@router.get("/batch/{batch_id}/download")
async def batch_download(
    batch_id: str,
    session: Session = Depends(get_session),
):
    """下载合并后的音频文件。"""
    from app.models.batch_job import BatchJob

    batch_job = session.get(BatchJob, batch_id)
    if not batch_job:
        raise VoiceLabError("Batch job not found", "BATCH_NOT_FOUND")
    if not batch_job.merged_audio_asset_id:
        raise VoiceLabError("Merged audio not ready yet", "AUDIO_NOT_READY")

    audio = voice_asset_repo.get_audio_asset(session, batch_job.merged_audio_asset_id)
    if not audio:
        raise VoiceLabError("Merged audio asset not found", "ASSET_NOT_FOUND")

    path = Path(audio.file_path)
    if not path.exists():
        raise VoiceLabError("Merged audio file not found on disk", "FILE_NOT_FOUND")

    return FileResponse(
        path,
        media_type={"mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac"}.get(audio.format, "application/octet-stream"),
        filename=f"{batch_id}.{audio.format}",
    )


@router.post("/batch/{batch_id}/retry", response_model=BatchSubmitResponse)
async def batch_retry(
    batch_id: str,
    session: Session = Depends(get_session),
):
    """重试失败的段。"""
    return await service.retry_failed(session, batch_id)
