import json

from sqlmodel import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.domain.schemas import (
    AudioAssetResponse,
    ProviderVoicePreviewRequest,
    ProviderVoicePreviewResponse,
)
from app.providers.registry import get_provider
from app.services.asset_service import AssetService
from app.services.cost_guard_service import CostGuardService
from app.services.text_preprocess_service import TextPreprocessService
from app.utils.id_generator import new_id


class VoicePreviewService:
    def __init__(self):
        self.preprocessor = TextPreprocessService()
        self.asset_service = AssetService()
        self.cost_guard = CostGuardService()
        self.logger = get_logger("voice_preview")

    async def preview(
        self,
        session: Session,
        request: ProviderVoicePreviewRequest,
    ) -> ProviderVoicePreviewResponse:
        settings = get_settings()
        adapter = get_provider(request.provider)

        processed_text = self.preprocessor.preprocess(request.text)
        voice_params = {}
        if request.speed is not None:
            voice_params["speed"] = request.speed
        if request.vol is not None:
            voice_params["vol"] = request.vol
        if request.pitch is not None:
            voice_params["pitch"] = request.pitch
        if request.emotion is not None:
            voice_params["emotion"] = request.emotion

        audio_params = {
            "format": request.audio_format,
            "sample_rate": settings.default_sample_rate,
            "bitrate": settings.default_bitrate,
            "channel": settings.default_channel,
        }

        plan = RenderPlan(
            id=new_id("preview"),
            text=request.text,
            processed_text=processed_text,
            profile_id="__preview__",
            provider=request.provider,
            model=request.model,
            provider_voice_id=request.provider_voice_id,
            voice_params=voice_params,
            audio_params=audio_params,
            subtitle=SubtitlePlan(enabled=False),
            output_format=request.output_format,
        )

        self.logger.info(
            "preview_start provider=%s voice_id=%s model=%s text_length=%d",
            request.provider, request.provider_voice_id, request.model, len(request.text),
        )

        self.cost_guard.require_confirmed(
            request.provider, "binding_voice_preview", request.confirm_cost
        )

        result = await adapter.render_sync(plan)
        audio_asset, _ = self.asset_service.save_assets(
            session,
            job_id=new_id("preview_job"),
            provider=request.provider,
            model=request.model,
            result=result,
            audio_params=audio_params,
            subtitle_type="sentence",
        )

        self.logger.info(
            "preview_success provider=%s voice_id=%s duration_ms=%s",
            request.provider, request.provider_voice_id, result.duration_ms,
        )

        return ProviderVoicePreviewResponse(
            audio_asset=AudioAssetResponse(
                id=audio_asset.id,
                url=audio_asset.file_url,
                duration_ms=audio_asset.duration_ms,
                format=audio_asset.format,
            ),
            provider=request.provider,
            model=request.model,
            provider_voice_id=request.provider_voice_id,
        )