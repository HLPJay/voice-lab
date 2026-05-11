import json

from sqlmodel import Session

from app.core.config import get_settings
from app.core.errors import BindingNotFound, ProfileNotFound, ProviderError, UnsupportedProvider, VoiceLabError
from app.core.time import utc_now_iso
from app.domain.enums import JobStatus, JobType, Provider
from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.domain.schemas import (
    AudioAssetResponse,
    SubtitleAssetResponse,
    VoiceRenderRequest,
    VoiceRenderResponse,
)
from app.models.voice_job import VoiceJob
from app.providers.minimax_speech_adapter import MiniMaxSpeechAdapter
from app.providers.mock_speech_adapter import MockSpeechAdapter
from app.repositories.voice_profile_repo import get_binding, get_profile
from app.services.asset_service import AssetService
from app.services.text_preprocess_service import TextPreprocessService
from app.utils.id_generator import new_id


class VoiceRenderService:
    def __init__(self):
        self.preprocessor = TextPreprocessService()
        self.asset_service = AssetService()

    def _provider(self, provider: str):
        if provider == "mock":
            return MockSpeechAdapter()
        if provider == "minimax":
            return MiniMaxSpeechAdapter()
        raise UnsupportedProvider(f"Unsupported provider: {provider}", provider)

    async def render_voice(
        self,
        session: Session,
        request: VoiceRenderRequest,
        voice_overrides: dict | None = None,
    ) -> VoiceRenderResponse:
        settings = get_settings()
        provider = request.provider or settings.voice_provider
        if provider not in Provider.__members__:
            raise UnsupportedProvider(f"Unsupported provider: {provider}", provider)
        profile = get_profile(session, request.profile_id)
        if not profile:
            raise ProfileNotFound("Voice profile not found", request.profile_id)
        binding = get_binding(session, request.profile_id, provider)
        if not binding and provider == Provider.mock and settings.mock_fallback_provider:
            binding = get_binding(session, request.profile_id, settings.mock_fallback_provider)
        if not binding:
            raise BindingNotFound("No available voice binding found", f"profile={request.profile_id}, provider={provider}")

        processed_text = self.preprocessor.preprocess(request.text)
        voice_params = json.loads(binding.params_json or "{}")
        if voice_overrides:
            voice_params.update({k: v for k, v in voice_overrides.items() if v is not None})
        audio_params = {
            "format": settings.default_audio_format,
            "sample_rate": settings.default_sample_rate,
            "bitrate": settings.default_bitrate,
            "channel": settings.default_channel,
        }
        plan = RenderPlan(
            id=new_id("plan"),
            text=request.text,
            processed_text=processed_text,
            profile_id=profile.id,
            provider=provider,
            model=binding.model,
            provider_voice_id=binding.provider_voice_id,
            voice_params=voice_params,
            audio_params=audio_params,
            subtitle=SubtitlePlan(enabled=request.need_subtitle, type="sentence"),
            output_format="hex" if request.output_format == "mp3" else request.output_format,
        )
        now = utc_now_iso()
        job = VoiceJob(
            id=new_id("job"),
            job_type=JobType.sync_render,
            status=JobStatus.pending,
            provider=provider,
            model=plan.model,
            profile_id=profile.id,
            binding_id=binding.id,
            input_text=request.text,
            processed_text=processed_text,
            render_plan_json=plan.model_dump_json(),
            created_at=now,
            updated_at=now,
        )
        session.add(job)
        session.commit()

        try:
            job.status = JobStatus.running
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
            result = await self._provider(provider).render_sync(plan)
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
            exc.job_id = job.id
            raise
        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
            raise ProviderError("Voice render failed", str(exc), job_id=job.id) from exc
