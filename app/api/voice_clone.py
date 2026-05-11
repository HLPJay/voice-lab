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
    file_data = await file.read()
    return await service.upload_audio(provider, file_data, file.filename, purpose)


@router.post("/clone/create", response_model=VoiceCloneResponse)
async def create_clone(
    request: VoiceCloneRequest,
    provider: str = Query(default="mock"),
):
    return await service.clone_voice(provider, request)