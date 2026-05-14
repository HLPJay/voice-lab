from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import VoiceRenderRequest, VoiceRenderResponse
from app.services.capability_validator import capability_validator
from app.services.voice_render_service import VoiceRenderService

router = APIRouter()
service = VoiceRenderService()


@router.post("/render", response_model=VoiceRenderResponse)
async def render_voice(
    request: VoiceRenderRequest,
    session: Session = Depends(get_session),
):
    capability_validator.validate_tts(
        provider=request.provider,
        text=request.text,
        audio_format=request.audio_format,
        need_subtitle=request.need_subtitle,
        speed=request.speed,
        vol=request.vol,
        pitch=request.pitch,
        emotion=request.emotion,
    )
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
