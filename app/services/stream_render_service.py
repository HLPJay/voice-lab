import base64
import json
from typing import AsyncGenerator

from sqlmodel import Session

from app.core.config import get_settings
from app.core.errors import BindingNotFound, ProfileNotFound, ProviderError, VoiceLabError
from app.core.logging import get_logger
from app.core.time import utc_now_iso
from app.domain.enums import JobStatus, JobType
from app.domain.render_plan import RenderPlan, SubtitlePlan
from app.domain.schemas import StreamRenderRequest
from app.models.voice_asset import AudioAsset
from app.models.voice_job import VoiceJob
from app.providers.registry import get_provider
from app.repositories import voice_asset_repo
from app.repositories.voice_profile_repo import get_binding, get_profile
from app.services.asset_service import AssetService
from app.services.text_preprocess_service import TextPreprocessService
from app.utils.files import storage_path
from app.utils.id_generator import new_id

logger = get_logger("stream_render")


class StreamRenderService:
    def __init__(self):
        self.preprocessor = TextPreprocessService()
        self.asset_service = AssetService()

    async def render_stream(
        self, session: Session, request: StreamRenderRequest
    ) -> AsyncGenerator[dict, None]:
        """
        流式语音生成。yield dict 消息给调用方（WebSocket 端点）。

        消息类型：
        - {"event": "started", ...}
        - {"event": "audio_chunk", ...}  （多次）
        - {"event": "completed", ...}
        - {"event": "error", ...}
        """
        settings = get_settings()
        provider = request.provider or settings.voice_provider
        get_provider(provider)

        profile = get_profile(session, request.profile_id)
        if not profile:
            raise ProfileNotFound("Voice profile not found", request.profile_id)

        binding = get_binding(session, request.profile_id, provider)
        if not binding and provider == "mock" and settings.mock_fallback_provider:
            binding = get_binding(session, request.profile_id, settings.mock_fallback_provider)
        if not binding:
            raise BindingNotFound(
                "No available voice binding found",
                f"profile={request.profile_id}, provider={provider}",
            )

        processed_text = self.preprocessor.preprocess(request.text)
        voice_params = json.loads(binding.params_json or "{}")
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
            subtitle=SubtitlePlan(enabled=False),
            output_format="hex" if request.output_format == "mp3" else request.output_format,
        )

        job = VoiceJob(
            id=new_id("job"),
            job_type=JobType.stream_render,
            status=JobStatus.running,
            provider=provider,
            model=plan.model,
            profile_id=profile.id,
            binding_id=binding.id,
            input_text=request.text,
            processed_text=processed_text,
            render_plan_json=plan.model_dump_json(),
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        session.add(job)
        session.commit()

        logger.info(
            "stream_render_start job=%s profile=%s provider=%s text_length=%d",
            job.id, request.profile_id, provider, len(request.text),
        )

        try:
            yield {
                "event": "started",
                "job_id": job.id,
                "provider": provider,
                "model": plan.model,
            }

            adapter = get_provider(provider)
            all_audio_data = bytearray()
            chunk_count = 0
            total_duration_ms = 0
            total_characters = 0

            async for chunk in adapter.render_stream(plan):
                all_audio_data.extend(chunk.audio_data)
                chunk_count += 1
                if chunk.duration_ms:
                    total_duration_ms += chunk.duration_ms
                if chunk.usage_characters:
                    total_characters = chunk.usage_characters

                yield {
                    "event": "audio_chunk",
                    "chunk_index": chunk.chunk_index,
                    "audio_base64": base64.b64encode(chunk.audio_data).decode(),
                    "duration_ms": chunk.duration_ms,
                    "is_final": chunk.is_final,
                }

            # 保存完整音频
            audio_id = new_id("audio")
            fmt = request.output_format or "mp3"
            audio_path = storage_path("audio", f"{audio_id}.{fmt}")
            audio_path.write_bytes(bytes(all_audio_data))

            audio_asset = AudioAsset(
                id=audio_id,
                job_id=job.id,
                provider=provider,
                model=plan.model,
                file_path=str(audio_path),
                file_url=f"/api/voice/assets/{audio_id}/download",
                format=fmt,
                duration_ms=total_duration_ms or None,
                usage_characters=total_characters or None,
                created_at=utc_now_iso(),
            )
            voice_asset_repo.create_audio_asset(session, audio_asset)

            job.status = JobStatus.success
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()

            logger.info(
                "stream_render_success job=%s chunks=%d duration_ms=%d characters=%d",
                job.id, chunk_count, total_duration_ms, total_characters,
            )

            yield {
                "event": "completed",
                "job_id": job.id,
                "total_chunks": chunk_count,
                "total_duration_ms": total_duration_ms,
                "total_characters": total_characters,
                "audio_asset": {
                    "id": audio_asset.id,
                    "url": audio_asset.file_url,
                },
            }

        except VoiceLabError as exc:
            job.status = JobStatus.failed
            job.error_message = exc.message
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
            logger.error("stream_render_failed job=%s error=%s", job.id, exc.message)
            yield {"event": "error", "code": exc.error_code or "PROVIDER_ERROR", "message": exc.message}
        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)[:500]
            job.updated_at = utc_now_iso()
            session.add(job)
            session.commit()
            logger.error("stream_render_failed job=%s error=%s", job.id, str(exc))
            yield {"event": "error", "code": "INTERNAL_ERROR", "message": str(exc)[:200]}
