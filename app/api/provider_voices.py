from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import ProviderVoiceImportRequest, ProviderVoiceImportResponse, ProviderVoiceListResponse, ProviderVoicePreviewRequest, ProviderVoicePreviewResponse
from app.services.capability_validator import capability_validator
from app.services.voice_catalog_service import VoiceCatalogService
from app.services.provider_voice_import_service import ProviderVoiceImportService
from app.services.provider_voice_preview_service import ProviderVoicePreviewService

router = APIRouter()
service = VoiceCatalogService()
preview_service = ProviderVoicePreviewService()
import_service = ProviderVoiceImportService()


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
    capability_validator.validate_provider_voice_preview(
        provider=request.provider,
        text=request.text,
        audio_format=request.audio_format,
        need_subtitle=request.need_subtitle,
        speed=request.speed,
        vol=request.vol,
        pitch=request.pitch,
        emotion=request.emotion,
        model=request.model,
    )
    return await preview_service.preview(session, request.provider, request)


@router.post("/provider-voices/import", response_model=ProviderVoiceImportResponse)
async def import_provider_voice(
    request: ProviderVoiceImportRequest,
    session: Session = Depends(get_session),
):
    """将 MiniMax 远端已存在的 voice_id 登记到本地 provider_voices 表。

    verify=true 时会先调用 direct preview 验证 voice_id 可用后再导入；
    verify=false 时直接导入（metadata.verified=false）。
    """
    capability_validator.validate_provider_voice_import(
        provider=request.provider,
        preview_text=request.preview_text,
        verify=request.verify,
        model=request.model,
        audio_format=request.audio_format,
    )
    return await import_service.import_voice(session, request)
