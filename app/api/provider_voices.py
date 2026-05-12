from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import ProviderVoiceListResponse, ProviderVoicePreviewRequest, ProviderVoicePreviewResponse
from app.services.voice_catalog_service import VoiceCatalogService
from app.services.voice_preview_service import VoicePreviewService

router = APIRouter()
service = VoiceCatalogService()
preview_service = VoicePreviewService()


@router.get("/provider-voices", response_model=ProviderVoiceListResponse)
async def list_provider_voices(
    provider: str = Query(default="minimax"),
    voice_type: str = Query(default="all"),
    refresh: bool = Query(default=False),
    session: Session = Depends(get_session),
):
    return await service.list_provider_voices(
        session,
        provider=provider,
        voice_type=voice_type,
        refresh=refresh,
    )


@router.post("/provider-voices/preview", response_model=ProviderVoicePreviewResponse)
async def preview_provider_voice(
    request: ProviderVoicePreviewRequest,
    session: Session = Depends(get_session),
):
    """直连试听 — 跳过 profile binding，直接用指定的 provider_voice_id 生成音频。"""
    return await preview_service.preview(session, request)
