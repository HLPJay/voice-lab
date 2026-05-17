import json

from sqlmodel import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.time import utc_now_iso
from app.domain.enums import JobStatus, JobType
from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.domain.schemas import (
    AudioAssetResponse,
    ProviderVoicePreviewRequest,
    ProviderVoicePreviewResponse,
)
from app.models.voice_job import VoiceJob
from app.providers.capability_registry import get_capability
from app.providers.registry import get_provider
from app.services.asset_service import AssetService
from app.services.cost_guard_service import CostGuardService
from app.services.resource_guard_service import get_resource_guard
from app.services.text_preprocess_service import TextPreprocessService
from app.utils.id_generator import new_id


class ProviderVoicePreviewService:
    def __init__(self):
        self.preprocessor = TextPreprocessService()
        self.asset_service = AssetService()
        self.cost_guard = CostGuardService()
        self.logger = get_logger("provider_voice_preview")

    async def preview(
        self,
        session: Session,
        provider: str,
        request: ProviderVoicePreviewRequest,
    ) -> ProviderVoicePreviewResponse:
        self.cost_guard.require_confirmed(provider, "provider_voice_preview", request.confirm_cost)

        settings = get_settings()
        adapter = get_provider(provider)
        cap = get_capability(provider)

        model = request.model or (cap.tts.default_model if cap.tts else None) or cap.default_model
        audio_format = request.audio_format or (cap.tts.audio_formats[0] if cap.tts and cap.tts.audio_formats else "mp3")

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
            "format": audio_format,
            "sample_rate": settings.default_sample_rate,
            "bitrate": settings.default_bitrate,
            "channel": settings.default_channel,
        }

        plan = RenderPlan(
            id=new_id("plan"),
            text=request.text,
            processed_text=processed_text,
            profile_id="provider_voice_preview",
            provider=provider,
            model=model,
            provider_voice_id=request.provider_voice_id,
            voice_params=voice_params,
            audio_params=audio_params,
            subtitle=SubtitlePlan(enabled=request.need_subtitle, type="sentence"),
            output_format=request.output_format,
        )

        now = utc_now_iso()
        job = VoiceJob(
            id=new_id("job"),
            job_type=JobType.sync_render,
            status=JobStatus.pending,
            provider=provider,
            model=model,
            profile_id="provider_voice_preview",
            input_text=request.text,
            processed_text=processed_text,
            render_plan_json=plan.model_dump_json(),
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        self.logger.info(
            "preview_start job_id=%s provider=%s voice_id=%s model=%s text_length=%d",
            job.id, provider, request.provider_voice_id, model, len(request.text),
        )

        try:
            job.status = JobStatus.running
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()

            async with get_resource_guard().guard(
                provider=provider,
                operation="voice_preview",
                model=model,
                job_id=job.id,
            ):
                result = await adapter.render_sync(plan)
            audio_asset, subtitle_asset = self.asset_service.save_assets(
                session,
                job_id=job.id,
                provider=provider,
                model=model,
                result=result,
                audio_params=audio_params,
                subtitle_type="sentence",
            )

            job.status = JobStatus.success
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()

            self.logger.info(
                "preview_success job_id=%s provider=%s voice_id=%s duration_ms=%s",
                job.id, provider, request.provider_voice_id, result.duration_ms,
            )

            return ProviderVoicePreviewResponse(
                job_id=job.id,
                status="success",
                provider=provider,
                model=model,
                provider_voice_id=request.provider_voice_id,
                audio_asset=AudioAssetResponse(
                    id=audio_asset.id,
                    url=audio_asset.file_url,
                    duration_ms=audio_asset.duration_ms,
                    format=audio_asset.format,
                ),
            )
        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)[:500]
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
            raise