from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import VoiceVariantGroupResponse, VoiceVariantRenderRequest
from app.services.voice_variant_service import VoiceVariantService

router = APIRouter()
service = VoiceVariantService()


@router.post("/variants/render", response_model=VoiceVariantGroupResponse)
async def render_variants(
    request: VoiceVariantRenderRequest,
    session: Session = Depends(get_session),
):
    return await service.render_variants(session, request)
