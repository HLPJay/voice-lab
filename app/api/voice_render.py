from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import VoiceRenderRequest, VoiceRenderResponse
from app.services.voice_render_service import VoiceRenderService

router = APIRouter()
service = VoiceRenderService()


@router.post("/render", response_model=VoiceRenderResponse)
async def render_voice(
    request: VoiceRenderRequest,
    session: Session = Depends(get_session),
):
    return await service.render_voice(session, request)
