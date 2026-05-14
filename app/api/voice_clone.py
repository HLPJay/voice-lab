from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import VoiceCloneRequest, VoiceCloneResponse, VoiceCloneUploadResponse
from app.services.capability_validator import capability_validator
from app.services.voice_clone_service import VoiceCloneService

router = APIRouter()
service = VoiceCloneService()


@router.post("/clone/upload", response_model=VoiceCloneUploadResponse)
async def upload_clone_audio(
    file: UploadFile = File(...),
    purpose: str = Form(default="voice_clone"),
    provider: str = Form(default="mock"),
):
    from app.core.config import get_settings
    settings = get_settings()
    max_bytes = settings.clone_audio_max_size_mb * 1024 * 1024

    file_data = await file.read()
    if len(file_data) > max_bytes:
        from fastapi import HTTPException
        raise HTTPException(status_code=413, detail=f"File too large: {len(file_data)} bytes exceeds limit of {max_bytes} bytes ({settings.clone_audio_max_size_mb}MB)")

    return await service.upload_audio(provider, file_data, file.filename, purpose)


@router.post("/clone/create", response_model=VoiceCloneResponse)
async def create_clone(
    request: VoiceCloneRequest,
    provider: str = Query(default="mock"),
    session: Session = Depends(get_session),
):
    capability_validator.validate_voice_clone(
        provider=provider,
        voice_id=request.voice_id,
        preview_text=request.preview_text,
        need_noise_reduction=request.need_noise_reduction,
        need_volume_normalization=request.need_volume_normalization,
    )
    return await service.clone_voice(session, provider, request)