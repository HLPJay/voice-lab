from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import VoiceDeleteRequest, VoiceDeleteResponse
from app.services.voice_delete_service import VoiceDeleteService

router = APIRouter()
service = VoiceDeleteService()


@router.post("/voices/delete", response_model=VoiceDeleteResponse)
async def delete_voice(
    request: VoiceDeleteRequest,
    provider: str = Query(default="mock"),
    session: Session = Depends(get_session),
):
    return await service.delete_voice(session, provider, request)
