import json

from sqlmodel import Session

from app.core.config import get_settings
from app.core.context import set_job_id
from app.core.logging import get_logger
from app.core.errors import ProviderError, VoiceLabError
from app.core.time import utc_now_iso
from app.domain.enums import JobStatus, JobType
from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.domain.schemas import (
    AudioAssetResponse,
    SubtitleAssetResponse,
    VoiceRenderRequest,
    VoiceRenderResponse,
)
from app.models.voice_job import VoiceJob
from app.providers.registry import get_provider
from app.repositories.voice_profile_repo import resolve_binding
from app.services.asset_service import AssetService
from app.services.binding_validation_service import validate_binding_provider_voice
from app.services.cost_guard_service import CostGuardService
from app.services.resource_guard_service import get_resource_guard
from app.services.text_preprocess_service import TextPreprocessService
from app.utils.id_generator import new_id


class VoiceRenderService:
    def __init__(self):
        self.preprocessor = TextPreprocessService()
        self.asset_service = AssetService()
        self.cost_guard = CostGuardService()
        self.logger = get_logger("voice_render")

    async def render_voice(
        self,
        session: Session,
        request: VoiceRenderRequest,
        voice_overrides: dict | None = None,
        resource_guard_already_acquired: bool = False,
        # resource_guard_already_acquired 仅用于已经由上层 Resource Guard 保护的内部编排调用，
        # 避免重复限流；外部 API 不应暴露或使用该参数。
    ) -> VoiceRenderResponse:
        settings = get_settings()
        provider = request.provider or settings.voice_provider
        get_provider(provider)  # validate provider is supported before binding lookup
        binding, resolved_provider = resolve_binding(session, request.profile_id, provider)
        provider = resolved_provider
        adapter = get_provider(provider)

        validate_binding_provider_voice(session, binding)

        processed_text = self.preprocessor.preprocess(request.text)
        voice_params = json.loads(binding.params_json or "{}")
        if voice_overrides:
            voice_params.update({k: v for k, v in voice_overrides.items() if v is not None})
        audio_params = {
            "format": request.audio_format,
            "sample_rate": settings.default_sample_rate,
            "bitrate": settings.default_bitrate,
            "channel": settings.default_channel,
        }
        plan = RenderPlan(
            id=new_id("plan"),
            text=request.text,
            processed_text=processed_text,
            profile_id=binding.profile_id,
            provider=provider,
            model=binding.model,
            provider_voice_id=binding.provider_voice_id,
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
            model=plan.model,
            profile_id=binding.profile_id,
            binding_id=binding.id,
            input_text=request.text,
            processed_text=processed_text,
            render_plan_json=plan.model_dump_json(),
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        est = self.cost_guard.estimate_t2a_cost(provider, plan.model, request.text)
        self.logger.info(
            "render_start job=%s profile=%s provider=%s model=%s text_length=%d billing_chars=%d estimated_cny=%.6f",
            job.id, binding.profile_id, provider, plan.model, len(request.text),
            est["billing_characters"], est["estimated_cost_cny"] or 0,
        )

        try:
            job.status = JobStatus.running
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()

            if resource_guard_already_acquired:
                # Already guarded by upper layer (e.g. VoiceVariantService), skip t2a_sync guard
                set_job_id(job.id)
                result = await get_provider(provider).render_sync(plan)
            else:
                async with get_resource_guard().guard(
                    provider=provider,
                    operation="t2a_sync",
                    model=plan.model,
                    job_id=job.id,
                ):
                    set_job_id(job.id)
                    result = await get_provider(provider).render_sync(plan)
            audio_asset, subtitle_asset = self.asset_service.save_assets(
                session,
                job_id=job.id,
                provider=provider,
                model=plan.model,
                result=result,
                audio_params=audio_params,
                subtitle_type=plan.subtitle.type,
            )
            job.status = JobStatus.success
            job.provider_trace_id = result.trace_id
            job.response_json = json.dumps(result.response_json, ensure_ascii=False)
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
            self.logger.info(
                "render_success job=%s provider=%s model=%s duration_ms=%s trace_id=%s characters=%s",
                job.id, provider, plan.model, result.duration_ms, result.trace_id, result.usage_characters,
            )
            return VoiceRenderResponse(
                job_id=job.id,
                status=job.status,
                audio_asset=AudioAssetResponse(
                    id=audio_asset.id,
                    url=audio_asset.file_url,
                    duration_ms=audio_asset.duration_ms,
                    format=audio_asset.format,
                ),
                subtitle_asset=SubtitleAssetResponse(
                    id=subtitle_asset.id,
                    url=f"/api/voice/assets/{subtitle_asset.id}/download",
                    timeline=json.loads(subtitle_asset.timeline_json),
                )
                if subtitle_asset
                else None,
                provider=provider,
                model=plan.model,
            )
        except VoiceLabError as exc:
            job.status = JobStatus.failed
            job.error_message = exc.message
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
            self.logger.error(
                "render_failed job=%s provider=%s error=%s",
                job.id, provider, exc.message if hasattr(exc, "message") else str(exc),
            )
            exc.job_id = job.id
            raise
        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
            self.logger.error(
                "render_failed job=%s provider=%s error=%s",
                job.id, provider, exc.message if hasattr(exc, "message") else str(exc),
            )
            raise ProviderError("Voice render failed", str(exc), job_id=job.id) from exc
