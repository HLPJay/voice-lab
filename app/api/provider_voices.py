from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import ProviderVoiceListResponse
from app.services.voice_catalog_service import VoiceCatalogService

router = APIRouter()
service = VoiceCatalogService()


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
