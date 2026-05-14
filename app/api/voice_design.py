from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import VoiceDesignRequest, VoiceDesignResponse
from app.services.capability_validator import capability_validator
from app.services.voice_design_service import VoiceDesignService

router = APIRouter()
service = VoiceDesignService()


@router.post("/design/create", response_model=VoiceDesignResponse)
async def create_design(
    request: VoiceDesignRequest,
    provider: str = Query(default="mock"),
    session: Session = Depends(get_session),
):
    capability_validator.validate_voice_design(
        provider=provider,
        prompt=request.prompt,
        preview_text=request.preview_text,
        voice_id=request.voice_id,
    )
    return await service.design_voice(session, provider, request)