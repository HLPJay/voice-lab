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
    voice_overrides = {}
    if request.speed is not None:
        voice_overrides["speed"] = request.speed
    if request.vol is not None:
        voice_overrides["vol"] = request.vol
    if request.pitch is not None:
        voice_overrides["pitch"] = request.pitch
    if request.emotion is not None:
        voice_overrides["emotion"] = request.emotion
    return await service.render_voice(session, request, voice_overrides=voice_overrides or None)
