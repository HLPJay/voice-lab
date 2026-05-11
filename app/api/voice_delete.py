from fastapi import APIRouter, Query

from app.domain.schemas import VoiceDeleteRequest, VoiceDeleteResponse
from app.services.voice_delete_service import VoiceDeleteService

router = APIRouter()
service = VoiceDeleteService()


@router.post("/voices/delete", response_model=VoiceDeleteResponse)
async def delete_voice(
    request: VoiceDeleteRequest,
    provider: str = Query(default="mock"),
):
    return await service.delete_voice(provider, request)