from fastapi import APIRouter, File, Form, Query, UploadFile

from app.domain.schemas import VoiceCloneRequest, VoiceCloneResponse, VoiceCloneUploadResponse
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
):
    return await service.clone_voice(provider, request)