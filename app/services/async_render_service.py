import json
from pathlib import Path

import httpx
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.errors import JobNotFound, ProviderError, VoiceLabError
from app.core.logging import get_logger
from app.core.time import utc_now_iso
from app.domain.enums import JobStatus, JobType
from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.domain.schemas import (
    AsyncJobStatusResponse,
    AsyncRenderRequest,
    AsyncRenderResponse,
    AudioAssetResponse,
    SubtitleAssetResponse,
)
from app.models.voice_asset import AudioAsset, SubtitleAsset
from app.models.voice_job import VoiceJob
from app.providers.registry import get_provider
from app.repositories import voice_asset_repo, voice_job_repo
from app.repositories.voice_profile_repo import resolve_binding
from app.services.asset_service import AssetService
from app.services.binding_validation_service import validate_binding_provider_voice
from app.services.cost_guard_service import CostGuardService
from app.services.resource_guard_service import get_resource_guard
from app.utils.files import storage_path
from app.utils.id_generator import new_id


class AsyncRenderService:
    def __init__(self):
        self.asset_service = AssetService()
        self.cost_guard = CostGuardService()
        self.logger = get_logger("async_render")

    async def submit_task(
        self,
        session: Session,
        request: AsyncRenderRequest,
    ) -> AsyncRenderResponse:
        """Submit an async voice generation task. Returns immediately with a job_id."""
        settings = get_settings()
        binding, resolved_provider = resolve_binding(
            session, request.profile_id, request.provider or settings.voice_provider
        )
        provider = resolved_provider
        get_provider(provider)  # validate provider
        validate_binding_provider_voice(session, binding)
        self.cost_guard.require_confirmed(provider, "async_render", request.confirm_cost)

        # Async mode: basic text cleaning only, no length limit
        processed_text = request.text.strip()

        voice_params = json.loads(binding.params_json or "{}")
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

        adapter = get_provider(provider)

        # 1. Create job with pending status before calling provider
        now = utc_now_iso()
        job = VoiceJob(
            id=new_id("job"),
            job_type=JobType.async_render,
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

        # 2. Call provider to create async task (protected by t2a_async_submit guard)
        try:
            async with get_resource_guard().guard(
                provider=provider,
                operation="t2a_async_submit",
                model=plan.model,
                job_id=job.id,
            ):
                task_result = await adapter.create_async_task(plan)
            job.status = JobStatus.processing
            job.provider_trace_id = task_result.trace_id
            job.response_json = json.dumps({
                "provider_task_id": task_result.provider_task_id,
                "task_metadata": task_result.metadata,
            }, ensure_ascii=False)
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
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
            job.error_message = str(exc)[:500]
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
            raise

        self.logger.info(
            "async_submit job=%s provider=%s model=%s text_length=%d task_id=%s",
            job.id, provider, plan.model, len(request.text), task_result.provider_task_id,
        )

        return AsyncRenderResponse(
            job_id=job.id,
            status=job.status,
            provider=provider,
            model=plan.model,
        )

    async def query_status(
        self,
        session: Session,
        job_id: str,
    ) -> AsyncJobStatusResponse:
        """Poll async task status. Downloads and saves assets if completed."""
        job = voice_job_repo.get_job(session, job_id)
        if not job:
            raise JobNotFound("Voice job not found", job_id=job_id)

        if job.status in (JobStatus.success, JobStatus.failed):
            return self._build_status_response(session, job)

        try:
            response_data = json.loads(job.response_json or "{}")
        except json.JSONDecodeError:
            response_data = {}
        provider_task_id = response_data.get("provider_task_id")
        if not provider_task_id:
            raise ProviderError("No provider task ID found for job", job_id)

        adapter = get_provider(job.provider)

        try:
            async with get_resource_guard().guard(
                provider=job.provider,
                operation="t2a_async_query_download",
                model=job.model,
                job_id=job.id,
            ):
                task_status = await adapter.query_async_task(provider_task_id)

                if task_status.status == "success" and task_status.file_url:
                    # Re-check status inside _complete_job to guard against race:
                    # another concurrent request may have already completed this job
                    await self._complete_job(session, job, task_status)
                elif task_status.status == "success" and not task_status.file_url:
                    # Success but no file_url — mark failed to avoid stuck processing
                    job.status = JobStatus.failed
                    job.error_message = "Async task succeeded but file_url missing"
                    job.updated_at = utc_now_iso()
                    session.add(job)
                    session.commit()
                    self.logger.error("async_failed job=%s error=%s", job.id, job.error_message)
                elif task_status.status in ("failed", "expired", "cancelled", "canceled", "timeout"):
                    job.status = JobStatus.failed
                    job.error_message = task_status.error_message or f"Async task {task_status.status}"
                    job.updated_at = utc_now_iso()
                    session.add(job)
                    session.commit()
                    self.logger.error("async_failed job=%s error=%s", job.id, job.error_message)
        except VoiceLabError:
            # Re-raise VoiceLabError (includes ResourceLimitExceeded) without changing job status.
            # Transient query/download failure does not mean the provider task itself failed.
            raise

        return self._build_status_response(session, job)

    async def _complete_job(self, session: Session, job: VoiceJob, task_status) -> None:
        """Download audio and save assets when async task succeeds."""
        from app.providers.base import ProviderRenderResult

        # Idempotency guard: skip if already completed by a concurrent request
        session.refresh(job)
        if job.status == JobStatus.success:
            return

        file_url = task_status.file_url
        settings = get_settings()
        fmt = "mp3"
        audio_id = new_id("audio_file")
        audio_path = storage_path("audio", f"{audio_id}.{fmt}")

        if file_url.startswith(("http://", "https://")):
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                resp = await client.get(file_url)
                resp.raise_for_status()
                audio_path.write_bytes(resp.content)
        else:
            # Local file path (used by mock adapter) — read directly
            local_path = Path(file_url).resolve()
            storage_dir = Path(settings.storage_dir).resolve()
            if not local_path.exists():
                raise ProviderError("Audio file not found", f"local path {file_url} does not exist")
            if not str(local_path).startswith(str(storage_dir)):
                raise ProviderError("Invalid file path", "path traversal attempt detected")
            audio_path.write_bytes(local_path.read_bytes())

        try:
            plan_data = json.loads(job.render_plan_json or "{}")
        except json.JSONDecodeError:
            plan_data = {}
        audio_params = plan_data.get("audio_params", {})
        subtitle_config = plan_data.get("subtitle", {})
        subtitle_type = subtitle_config.get("type", "sentence")

        timeline = task_status.metadata.get("timeline", [])
        if not timeline and subtitle_config.get("enabled"):
            duration_s = round((task_status.duration_ms or 0) / 1000, 2)
            timeline = [{"text": job.processed_text or job.input_text or "", "start": 0.0, "end": duration_s}]

        result = ProviderRenderResult(
            audio_path=str(audio_path),
            duration_ms=task_status.duration_ms,
            usage_characters=task_status.usage_characters,
            trace_id=task_status.trace_id,
            response_json=task_status.metadata.get("raw_response", {}),
            timeline=timeline,
            metadata=task_status.metadata,
        )

        audio_asset, subtitle_asset = self.asset_service.save_assets(
            session,
            job_id=job.id,
            provider=job.provider,
            model=job.model or "",
            result=result,
            audio_params=audio_params,
            subtitle_type=subtitle_type,
        )

        job.status = JobStatus.success
        job.provider_trace_id = task_status.trace_id
        job.updated_at = utc_now_iso()
        session.add(job)
        session.commit()

        self.logger.info(
            "async_success job=%s duration_ms=%s characters=%s",
            job.id, task_status.duration_ms, task_status.usage_characters,
        )

    def _build_status_response(self, session: Session, job: VoiceJob) -> AsyncJobStatusResponse:
        """Build status response including asset info if job is completed."""
        audio_asset_resp = None
        subtitle_asset_resp = None

        if job.status == JobStatus.success:
            audio = session.exec(
                select(AudioAsset).where(AudioAsset.job_id == job.id)
            ).first()
            if audio:
                audio_asset_resp = AudioAssetResponse(
                    id=audio.id,
                    url=audio.file_url,
                    duration_ms=audio.duration_ms,
                    format=audio.format,
                )

            subtitle = session.exec(
                select(SubtitleAsset).where(SubtitleAsset.job_id == job.id)
            ).first()
            if subtitle:
                subtitle_asset_resp = SubtitleAssetResponse(
                    id=subtitle.id,
                    url=f"/api/voice/assets/{subtitle.id}/download",
                    timeline=json.loads(subtitle.timeline_json or "[]"),
                )

        return AsyncJobStatusResponse(
            job_id=job.id,
            status=job.status,
            provider=job.provider,
            model=job.model,
            audio_asset=audio_asset_resp,
            subtitle_asset=subtitle_asset_resp,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
