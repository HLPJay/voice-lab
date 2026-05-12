import asyncio
import json

from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.errors import ProfileNotFound, VoiceLabError
from app.core.logging import get_logger
from app.core.time import utc_now_iso
from app.domain.enums import BatchStatus, JobStatus, JobType
from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.domain.schemas import (
    BatchSegmentStatus,
    BatchStatusResponse,
    BatchSubmitResponse,
    LongtextBatchRequest,
    ScriptBatchRequest,
)
from app.models.batch_job import BatchJob, BatchSegment
from app.models.voice_asset import AudioAsset, SubtitleAsset
from app.models.voice_job import VoiceJob
from app.providers.registry import get_provider
from app.repositories import voice_asset_repo, voice_job_repo
from app.repositories.voice_profile_repo import get_profile, resolve_binding
from app.services.asset_service import AssetService
from app.services.audio_merge_service import AudioMergeService
from app.services.text_segment_service import TextSegmentService
from app.utils.files import storage_path
from app.utils.id_generator import new_id
from app.utils.srt import timeline_to_srt


class BatchOrchestrationService:
    def __init__(self):
        self.segmenter = TextSegmentService()
        self.audio_merger = AudioMergeService()
        self.asset_service = AssetService()
        self.logger = get_logger("batch_orchestration")

    async def submit_longtext(
        self,
        session: Session,
        request: LongtextBatchRequest,
    ) -> BatchSubmitResponse:
        """提交长文本批量任务：分段 → 创建 BatchJob + Segments → 后台执行。"""
        settings = get_settings()
        binding, resolved_provider = resolve_binding(
            session, request.profile_id, request.provider or settings.voice_provider
        )
        provider = resolved_provider
        get_provider(provider)

        texts = self.segmenter.segment(
            request.text, strategy=request.segment_strategy, max_chars=request.max_segment_chars
        )
        if not texts:
            raise VoiceLabError("Text segmentation produced no segments", "EMPTY_SEGMENTS")

        now = utc_now_iso()
        batch_id = new_id("batch")
        config_json = json.dumps(request.model_dump(), ensure_ascii=False)

        batch_job = BatchJob(
            id=batch_id,
            mode="longtext",
            status=BatchStatus.pending,
            provider=provider,
            output_format=request.output_format,
            total_segments=len(texts),
            silence_between_ms=request.silence_between_ms,
            config_json=config_json,
            created_at=now,
            updated_at=now,
        )
        session.add(batch_job)

        for i, text in enumerate(texts):
            segment = BatchSegment(
                id=new_id("seg"),
                batch_job_id=batch_id,
                index=i,
                text=text,
                profile_id=request.profile_id,
                params_json=json.dumps(request.params or {}),
                status=BatchStatus.pending,
                created_at=now,
                updated_at=now,
            )
            session.add(segment)

        session.commit()

        self.logger.info(
            "batch_submit_longtext batch_id=%s segments=%d", batch_id, len(texts)
        )

        self._execute_with_session(batch_id, provider)

        return BatchSubmitResponse(
            batch_id=batch_id,
            mode="longtext",
            total_segments=len(texts),
            status=BatchStatus.pending,
        )

    async def submit_script(
        self,
        session: Session,
        request: ScriptBatchRequest,
    ) -> BatchSubmitResponse:
        """提交剧本批量任务：映射 script → 创建 BatchJob + Segments → 后台执行。"""
        settings = get_settings()
        provider = request.provider or settings.voice_provider
        get_provider(provider)

        now = utc_now_iso()
        batch_id = new_id("batch")
        config_json = json.dumps(request.model_dump(), ensure_ascii=False)

        batch_job = BatchJob(
            id=batch_id,
            mode="script",
            status=BatchStatus.pending,
            provider=provider,
            output_format=request.output_format,
            total_segments=len(request.script),
            silence_between_ms=request.silence_between_ms,
            config_json=config_json,
            created_at=now,
            updated_at=now,
        )
        session.add(batch_job)

        for i, line in enumerate(request.script):
            profile = get_profile(session, line.profile_id)
            if not profile:
                raise ProfileNotFound("Voice profile not found", line.profile_id)

            segment = BatchSegment(
                id=new_id("seg"),
                batch_job_id=batch_id,
                index=i,
                text=line.text,
                profile_id=line.profile_id,
                role=line.role,
                params_json=json.dumps(line.params or {}),
                status=BatchStatus.pending,
                created_at=now,
                updated_at=now,
            )
            session.add(segment)

        session.commit()

        self.logger.info(
            "batch_submit_script batch_id=%s segments=%d", batch_id, len(request.script)
        )

        self._execute_with_session(batch_id, provider)

        return BatchSubmitResponse(
            batch_id=batch_id,
            mode="script",
            total_segments=len(request.script),
            status=BatchStatus.pending,
        )

    def _execute_with_session(self, batch_job_id: str, provider: str) -> asyncio.Task:
        """Execute batch job with a fresh session. Returns the Task so callers can hold a reference."""
        async def _run() -> None:
            from app.core.database import get_session
            session = next(get_session())
            try:
                await self.execute(session, batch_job_id)
            finally:
                session.close()

        task = asyncio.create_task(_run())
        if task is not None:
            task.add_done_callback(self._log_task_error)
        return task

    def _log_task_error(self, task: asyncio.Task) -> None:
        """Log any exception that occurred in a background task."""
        if task.cancelled():
            return
        exc = task.exception()
        if exc:
            self.logger.error("background_task_exc error=%s", str(exc))

    async def _process_segment_isolated(
        self,
        semaphore: asyncio.Semaphore,
        segment_id: str,
        provider: str,
        output_format: str,
        config: dict,
        db_engine,
    ) -> tuple[str, str, str | None]:
        """在独立 Session 中处理单个 segment，返回 (segment_id, status, error_message)。"""
        async with semaphore:
            from sqlmodel import Session as SqlSession
            session = SqlSession(db_engine)
            try:
                segment = session.get(BatchSegment, segment_id)
                if not segment:
                    return (segment_id, BatchStatus.failed, "Segment not found")

                segment = await self._process_segment(
                    session, segment, provider, output_format, config
                )
                session.commit()
                return (segment_id, segment.status, None)
            except Exception as exc:
                self.logger.error(
                    "segment_failed segment_id=%s error=%s", segment_id, str(exc)
                )
                try:
                    segment = session.get(BatchSegment, segment_id)
                    if segment:
                        segment.status = BatchStatus.failed
                        segment.error_message = str(exc)[:500]
                        segment.updated_at = utc_now_iso()
                        session.add(segment)
                        session.commit()
                except Exception:
                    pass
                return (segment_id, BatchStatus.failed, str(exc)[:500])
            finally:
                session.close()

    async def execute(self, session: Session, batch_job_id: str) -> None:
        """执行批量任务：并发生成 → 合并 → 更新状态。"""
        db_engine = session.bind
        batch_job = session.get(BatchJob, batch_job_id)
        if not batch_job:
            self.logger.error("batch_execute batch_job_id=%s not found", batch_job_id)
            return

        batch_job.status = BatchStatus.running
        batch_job.updated_at = utc_now_iso()
        session.add(batch_job)
        session.commit()

        segments = list(session.exec(
            select(BatchSegment).where(
                BatchSegment.batch_job_id == batch_job_id
            ).order_by(BatchSegment.index)
        ).all())

        config = {}
        try:
            config = json.loads(batch_job.config_json or "{}")
        except json.JSONDecodeError:
            pass

        settings = get_settings()
        provider = batch_job.provider or settings.voice_provider
        output_format = batch_job.output_format or "mp3"
        silence_ms = batch_job.silence_between_ms or 300

        semaphore = asyncio.Semaphore(settings.batch_max_concurrency)
        pending_tasks = []

        for segment in segments:
            if segment.status == BatchStatus.success:
                continue
            pending_tasks.append(
                self._process_segment_isolated(
                    semaphore, segment.id, provider, output_format, config, db_engine
                )
            )

        if pending_tasks:
            await asyncio.gather(*pending_tasks)

        session.expire_all()

        segments = list(session.exec(
            select(BatchSegment).where(
                BatchSegment.batch_job_id == batch_job_id
            ).order_by(BatchSegment.index)
        ).all())

        success_audio_paths = []
        success_timelines = []
        success_durations = []

        for segment in segments:
            if segment.status == BatchStatus.success and segment.audio_asset_id:
                audio_asset = session.get(AudioAsset, segment.audio_asset_id)
                if audio_asset:
                    success_audio_paths.append(audio_asset.file_path)
                    subtitle_asset = session.exec(
                        select(SubtitleAsset).where(
                            SubtitleAsset.audio_asset_id == segment.audio_asset_id
                        ).limit(1)
                    ).one_or_none()
                    timeline = json.loads(subtitle_asset.timeline_json) if subtitle_asset else []
                    success_timelines.append(timeline)
                    success_durations.append(segment.duration_ms or 0)

        batch_job.completed_segments = sum(
            1 for s in segments if s.status == BatchStatus.success
        )
        batch_job.failed_segments = sum(
            1 for s in segments if s.status == BatchStatus.failed
        )
        batch_job.updated_at = utc_now_iso()
        session.add(batch_job)
        session.commit()

        merged_audio_path = None
        total_duration_ms = None

        if success_audio_paths:
            try:
                merged_audio_path = self.audio_merger.merge(
                    success_audio_paths, silence_ms, output_format
                )
                merged_timeline = self.audio_merger.merge_timelines(
                    success_timelines, success_durations, silence_ms
                )

                now = utc_now_iso()
                merged_audio_id = new_id("audio")
                merged_audio_asset = AudioAsset(
                    id=merged_audio_id,
                    job_id=batch_job_id,
                    provider=provider,
                    file_path=merged_audio_path,
                    file_url=f"/api/voice/assets/{merged_audio_id}/download",
                    format=output_format,
                    duration_ms=sum(success_durations) + (
                        silence_ms * (len(success_durations) - 1)
                        if len(success_durations) > 1 else 0
                    ),
                    created_at=now,
                )
                voice_asset_repo.create_audio_asset(session, merged_audio_asset)

                if merged_timeline:
                    merged_subtitle_id = new_id("subtitle")
                    subtitle_json_path = storage_path("subtitles", f"{merged_subtitle_id}.json")
                    subtitle_srt_path = storage_path("subtitles", f"{merged_subtitle_id}.srt")
                    subtitle_json_path.write_text(
                        json.dumps(merged_timeline, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    subtitle_srt_path.write_text(timeline_to_srt(merged_timeline), encoding="utf-8")

                    merged_subtitle_asset = SubtitleAsset(
                        id=merged_subtitle_id,
                        job_id=batch_job_id,
                        audio_asset_id=merged_audio_id,
                        subtitle_type="sentence",
                        file_path=str(subtitle_json_path),
                        srt_path=str(subtitle_srt_path),
                        timeline_json=json.dumps(merged_timeline, ensure_ascii=False),
                        created_at=now,
                    )
                    voice_asset_repo.create_subtitle_asset(session, merged_subtitle_asset)
                    batch_job.merged_subtitle_asset_id = merged_subtitle_id

                batch_job.merged_audio_asset_id = merged_audio_id
                total_duration_ms = sum(success_durations) + (
                    silence_ms * (len(success_durations) - 1)
                    if len(success_durations) > 1 else 0
                )
            except Exception as exc:
                self.logger.error("merge_failed batch_id=%s error=%s", batch_job_id, str(exc))

        failed_count = sum(1 for s in segments if s.status == BatchStatus.failed)
        if failed_count == len(segments):
            batch_job.status = BatchStatus.failed
        elif failed_count > 0:
            batch_job.status = BatchStatus.partial
        else:
            batch_job.status = BatchStatus.success

        batch_job.updated_at = utc_now_iso()
        session.add(batch_job)
        session.commit()

        self.logger.info(
            "batch_complete batch_id=%s status=%s success=%d failed=%d duration_ms=%s",
            batch_job_id, batch_job.status,
            sum(1 for s in segments if s.status == BatchStatus.success),
            failed_count,
            total_duration_ms,
        )

    async def _process_segment(
        self,
        session: Session,
        segment: BatchSegment,
        provider: str,
        output_format: str,
        config: dict,
    ) -> BatchSegment:
        """Process a single segment: render audio and save asset."""
        settings = get_settings()
        binding, resolved_provider = resolve_binding(session, segment.profile_id, provider)
        provider = resolved_provider

        voice_params = json.loads(binding.params_json or "{}")
        segment_params = json.loads(segment.params_json or "{}")
        voice_params.update({k: v for k, v in segment_params.items() if v is not None})

        audio_params = {
            "format": output_format,
            "sample_rate": settings.default_sample_rate,
            "bitrate": settings.default_bitrate,
            "channel": settings.default_channel,
        }

        plan = RenderPlan(
            id=new_id("plan"),
            text=segment.text,
            processed_text=segment.text,
            profile_id=segment.profile_id,
            provider=provider,
            model=binding.model,
            provider_voice_id=binding.provider_voice_id,
            voice_params=voice_params,
            audio_params=audio_params,
            subtitle=SubtitlePlan(enabled=config.get("need_subtitle", True), type="sentence"),
            output_format=output_format,
        )

        now = utc_now_iso()
        voice_job = voice_job_repo.create_job(session, VoiceJob(
            id=new_id("job"),
            job_type=JobType.sync_render,
            status=JobStatus.pending,
            provider=provider,
            model=binding.model,
            profile_id=segment.profile_id,
            binding_id=binding.id,
            input_text=segment.text,
            processed_text=segment.text,
            render_plan_json=plan.model_dump_json(),
            created_at=now,
            updated_at=now,
        ))

        voice_job.status = JobStatus.running
        voice_job.updated_at = utc_now_iso()
        session.add(voice_job)
        session.commit()

        result = await get_provider(provider).render_sync(plan)

        audio_asset, subtitle_asset = self.asset_service.save_assets(
            session,
            job_id=voice_job.id,
            provider=provider,
            model=binding.model,
            result=result,
            audio_params=audio_params,
            subtitle_type="sentence",
        )

        segment.status = BatchStatus.success
        segment.voice_job_id = voice_job.id
        segment.audio_asset_id = audio_asset.id
        segment.duration_ms = result.duration_ms
        segment.updated_at = utc_now_iso()
        session.add(segment)

        voice_job.status = JobStatus.success
        voice_job.provider_trace_id = result.trace_id
        voice_job.response_json = json.dumps(result.response_json, ensure_ascii=False)
        voice_job.updated_at = utc_now_iso()
        session.add(voice_job)
        session.commit()

        return segment

    async def get_status(self, session: Session, batch_job_id: str) -> BatchStatusResponse:
        """查询批量任务进度。"""
        batch_job = session.get(BatchJob, batch_job_id)
        if not batch_job:
            raise VoiceLabError("Batch job not found", "BATCH_NOT_FOUND")

        segments = list(session.exec(
            select(BatchSegment).where(
                BatchSegment.batch_job_id == batch_job_id
            ).order_by(BatchSegment.index)
        ).all())

        segment_statuses = [
            BatchSegmentStatus(
                index=s.index,
                role=s.role,
                text_preview=(s.text or "")[:30],
                status=s.status,
                duration_ms=s.duration_ms,
                audio_asset_id=s.audio_asset_id,
                error_message=s.error_message,
            )
            for s in segments
        ]

        merged_audio = None
        merged_subtitle = None
        total_duration_ms = None

        if batch_job.merged_audio_asset_id:
            merged_audio = {
                "id": batch_job.merged_audio_asset_id,
                "url": f"/api/voice/assets/{batch_job.merged_audio_asset_id}/download",
            }
            merged_asset = session.get(AudioAsset, batch_job.merged_audio_asset_id)
            if merged_asset:
                total_duration_ms = merged_asset.duration_ms

        if batch_job.merged_subtitle_asset_id:
            merged_subtitle = {
                "id": batch_job.merged_subtitle_asset_id,
                "url": f"/api/voice/assets/{batch_job.merged_subtitle_asset_id}/download",
            }

        return BatchStatusResponse(
            batch_id=batch_job.id,
            mode=batch_job.mode,
            status=batch_job.status,
            total_segments=batch_job.total_segments,
            completed_segments=batch_job.completed_segments,
            failed_segments=batch_job.failed_segments,
            segments=segment_statuses,
            merged_audio=merged_audio,
            merged_subtitle=merged_subtitle,
            total_duration_ms=total_duration_ms,
            created_at=batch_job.created_at,
            updated_at=batch_job.updated_at,
        )

    async def retry_failed(
        self, session: Session, batch_job_id: str
    ) -> BatchSubmitResponse:
        """重试失败的段。"""
        batch_job = session.get(BatchJob, batch_job_id)
        if not batch_job:
            raise VoiceLabError("Batch job not found", "BATCH_NOT_FOUND")

        failed_segments = list(session.exec(
            select(BatchSegment).where(
                BatchSegment.batch_job_id == batch_job_id,
                BatchSegment.status == BatchStatus.failed,
            ).order_by(BatchSegment.index)
        ).all())

        if not failed_segments:
            return BatchSubmitResponse(
                batch_id=batch_job_id,
                mode=batch_job.mode,
                total_segments=batch_job.total_segments,
                status=batch_job.status,
                message="No failed segments to retry",
            )

        now = utc_now_iso()
        for seg in failed_segments:
            seg.status = BatchStatus.pending
            seg.error_message = None
            seg.updated_at = now
            session.add(seg)

        batch_job.status = BatchStatus.running
        batch_job.updated_at = now
        session.add(batch_job)
        session.commit()

        self._execute_with_session(batch_job_id, batch_job.provider)

        return BatchSubmitResponse(
            batch_id=batch_job_id,
            mode=batch_job.mode,
            total_segments=batch_job.total_segments,
            status=BatchStatus.running,
            message=f"Retrying {len(failed_segments)} failed segments",
        )
