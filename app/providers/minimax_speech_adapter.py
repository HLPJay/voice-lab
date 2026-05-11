import binascii
import json as _json
import re
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.errors import ProviderError, ProviderNotConfigured
from app.domain.enums import ProviderVoiceStatus
from app.domain.render_plan import RenderPlan
from app.domain.schemas import ProviderVoiceRead
from app.providers.base import AsyncTaskResult, AsyncTaskStatus, ProviderRenderResult, SpeechProvider
from app.utils.audio import estimate_duration_ms
from app.utils.files import storage_path
from app.utils.id_generator import new_id

_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]+$")


class MiniMaxSpeechAdapter(SpeechProvider):
    provider_name = "minimax"

    def _description_to_text(self, value) -> str | None:
        if isinstance(value, list):
            return "\n".join(str(item) for item in value if item)
        if value:
            return str(value)
        return None

    def _convert_voice_response(self, body: dict) -> list[ProviderVoiceRead]:
        groups = {
            "system_voice": "system",
            "voice_cloning": "voice_cloning",
            "voice_generation": "voice_generation",
        }
        voices: list[ProviderVoiceRead] = []
        for response_key, voice_type in groups.items():
            for item in body.get(response_key) or []:
                provider_voice_id = item.get("voice_id")
                if not provider_voice_id:
                    continue
                voices.append(
                    ProviderVoiceRead(
                        id=f"minimax_{provider_voice_id}",
                        provider=self.provider_name,
                        provider_voice_id=provider_voice_id,
                        voice_type=voice_type,
                        name=item.get("voice_name") or provider_voice_id,
                        description=self._description_to_text(item.get("description")),
                        language=item.get("language"),
                        gender=item.get("gender"),
                        status=ProviderVoiceStatus.available,
                        provider_created_time=item.get("created_time"),
                        metadata={"raw": item},
                    )
                )
        return voices

    def _is_hex_string(self, value: str) -> bool:
        if not isinstance(value, str):
            return False
        if len(value) % 2 != 0:
            return False
        return bool(_HEX_PATTERN.match(value))

    async def _download_content(self, url: str, timeout: float) -> bytes:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def _save_audio_from_data(
        self,
        data: dict,
        output_format: str,
        audio_params: dict,
        timeout: float,
    ) -> tuple[Path, str]:
        fmt = audio_params.get("format", "mp3")
        audio_path = storage_path("audio", f"{new_id('audio_file')}.{fmt}")

        audio_url = data.get("audio_url") or data.get("url")
        audio_hex = data.get("audio")

        if output_format == "url" and audio_url:
            content = await self._download_content(audio_url, timeout)
            audio_path.write_bytes(content)
        elif isinstance(audio_hex, str) and audio_hex.startswith(("http://", "https://")):
            content = await self._download_content(audio_hex, timeout)
            audio_path.write_bytes(content)
        elif audio_hex and self._is_hex_string(audio_hex):
            audio_path.write_bytes(binascii.unhexlify(audio_hex))
        elif audio_url:
            content = await self._download_content(audio_url, timeout)
            audio_path.write_bytes(content)
        else:
            raise ProviderError(
                "MiniMax audio save failed",
                "No valid audio source found in response (no hex, no URL)",
            )
        return audio_path, fmt

    def _normalize_timeline(self, raw_timeline: list[dict]) -> list[dict]:
        """Convert MiniMax timeline items to internal standard format (start/end in seconds).

        MiniMax returns time_begin/time_end in milliseconds. The internal standard
        uses start/end in seconds. Also normalizes field names and drops extra keys.
        """
        normalized = []
        for item in raw_timeline:
            entry = {
                "text": item.get("text", ""),
                "start": item.get("time_begin", item.get("start", 0)) / 1000,
                "end": item.get("time_end", item.get("end", 0)) / 1000,
            }
            normalized.append(entry)
        return normalized

    async def _extract_timeline_from_subtitle_file(
        self,
        subtitle_file: str | list | None,
        timeout: float,
    ) -> tuple[list[dict], dict]:
        timeline: list[dict] = []
        metadata: dict = {}

        if isinstance(subtitle_file, list):
            timeline = subtitle_file
        elif isinstance(subtitle_file, str) and subtitle_file.startswith("http"):
            metadata["subtitle_file_url_downloaded"] = True
            try:
                content = await self._download_content(subtitle_file, timeout)
                text = content.decode("utf-8")
                parsed = _json.loads(text)
                if isinstance(parsed, list):
                    timeline = parsed
                elif isinstance(parsed, dict):
                    for key in ("sentences", "items", "timeline", "words"):
                        if key in parsed and isinstance(parsed[key], list):
                            timeline = parsed[key]
                            break
            except Exception:
                metadata["subtitle_file_parse_failed"] = True

        timeline = self._normalize_timeline(timeline)
        return timeline, metadata

    async def list_voices(self, voice_type: str = "all") -> list[ProviderVoiceRead]:
        settings = get_settings()
        if not settings.minimax_api_key or settings.minimax_api_key == "replace_me":
            raise ProviderNotConfigured("MiniMax API key is missing", "Set MINIMAX_API_KEY or use provider=mock")

        url = settings.minimax_base_url.rstrip("/") + "/v1/get_voice"
        try:
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}", "Content-Type": "application/json"},
                    json={"voice_type": voice_type},
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise ProviderError("MiniMax voice list request failed", str(exc)) from exc

        base_resp = body.get("base_resp") or {}
        if base_resp.get("status_code") not in (None, 0):
            raise ProviderError("MiniMax voice list request failed", base_resp.get("status_msg"))
        return self._convert_voice_response(body)

    async def render_sync(self, plan: RenderPlan) -> ProviderRenderResult:
        settings = get_settings()
        if not settings.minimax_api_key or settings.minimax_api_key == "replace_me":
            raise ProviderNotConfigured("MiniMax API key is missing", "Set MINIMAX_API_KEY or use provider=mock")

        voice_setting = {"voice_id": plan.provider_voice_id, **plan.voice_params}
        if not voice_setting.get("emotion"):
            voice_setting.pop("emotion", None)
        payload = {
            "model": plan.model,
            "text": plan.processed_text,
            "stream": False,
            "language_boost": plan.language_boost,
            "output_format": plan.output_format,
            "voice_setting": voice_setting,
            "audio_setting": plan.audio_params,
            "subtitle_enable": plan.subtitle.enabled,
            "subtitle_type": plan.subtitle.type,
        }
        url = settings.minimax_base_url.rstrip("/") + settings.minimax_t2a_path
        try:
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise ProviderError("MiniMax request failed", str(exc)) from exc

        trace_id = body.get("trace_id")
        data = body.get("data") or {}
        extra = body.get("extra_info") or {}

        try:
            audio_path, fmt = await self._save_audio_from_data(
                data, plan.output_format, plan.audio_params, settings.minimax_timeout_seconds
            )
        except Exception as exc:
            raise ProviderError("MiniMax audio save failed", str(exc)) from exc

        subtitle_file = data.get("subtitle") or data.get("subtitle_file")
        timeline, subtitle_meta = await self._extract_timeline_from_subtitle_file(
            subtitle_file, settings.minimax_timeout_seconds
        )

        duration_ms = extra.get("audio_length") or extra.get("duration_ms") or estimate_duration_ms(plan.text)
        metadata = {"extra_info": extra}
        metadata.update(subtitle_meta)

        return ProviderRenderResult(
            audio_path=str(Path(audio_path)),
            duration_ms=duration_ms,
            usage_characters=extra.get("usage_characters") or len(plan.text),
            trace_id=trace_id,
            response_json=body,
            timeline=timeline,
            metadata=metadata,
        )

    async def create_async_task(self, plan: RenderPlan) -> AsyncTaskResult:
        settings = get_settings()
        if not settings.minimax_api_key or settings.minimax_api_key == "replace_me":
            raise ProviderNotConfigured("MiniMax API key is missing", "Set MINIMAX_API_KEY")

        voice_setting = {"voice_id": plan.provider_voice_id, **plan.voice_params}
        if not voice_setting.get("emotion"):
            voice_setting.pop("emotion", None)
        payload = {
            "model": plan.model,
            "text": plan.processed_text,
            "stream": False,
            "language_boost": plan.language_boost,
            "output_format": plan.output_format,
            "voice_setting": voice_setting,
            "audio_setting": plan.audio_params,
            "subtitle_enable": plan.subtitle.enabled,
            "subtitle_type": plan.subtitle.type,
        }
        url = settings.minimax_base_url.rstrip("/") + settings.minimax_async_t2a_path
        try:
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise ProviderError("MiniMax async task creation failed", str(exc)) from exc

        base_resp = body.get("base_resp") or {}
        if base_resp.get("status_code") not in (None, 0):
            raise ProviderError("MiniMax async task creation failed", base_resp.get("status_msg"))

        task_id = body.get("task_id")
        if not task_id:
            raise ProviderError("MiniMax async task creation failed", "No task_id in response")
        task_id = str(task_id)

        return AsyncTaskResult(
            task_id=task_id,
            provider_task_id=task_id,
            status="processing",
            trace_id=body.get("trace_id"),
            metadata={"extra_info": body.get("extra_info") or {}},
        )

    async def query_async_task(self, provider_task_id: str) -> AsyncTaskStatus:
        settings = get_settings()
        if not settings.minimax_api_key or settings.minimax_api_key == "replace_me":
            raise ProviderNotConfigured("MiniMax API key is missing", "Set MINIMAX_API_KEY")

        url = settings.minimax_base_url.rstrip("/") + settings.minimax_async_query_path
        try:
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                response = await client.get(
                    url,
                    params={"task_id": provider_task_id},
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}"},
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise ProviderError("MiniMax async task query failed", str(exc)) from exc

        base_resp = body.get("base_resp") or {}
        if base_resp.get("status_code") not in (None, 0):
            raise ProviderError("MiniMax async task query failed", base_resp.get("status_msg"))

        status = (body.get("status") or "processing").lower()
        file_url = body.get("file_url") or body.get("audio_url")
        extra = body.get("extra_info") or {}

        if status == "success" and not file_url:
            file_id = body.get("file_id")
            if file_id:
                file_url = await self._retrieve_file_url(file_id, settings)

        return AsyncTaskStatus(
            task_id=provider_task_id,
            status=status,
            file_url=file_url,
            duration_ms=extra.get("audio_length") or extra.get("duration_ms"),
            usage_characters=extra.get("usage_characters"),
            trace_id=body.get("trace_id"),
            error_message=base_resp.get("status_msg") if status == "failed" else None,
            metadata={"raw_response": body},
        )

    async def _retrieve_file_url(self, file_id: int, settings) -> str | None:
        url = settings.minimax_base_url.rstrip("/") + "/v1/files/retrieve"
        try:
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                response = await client.get(
                    url,
                    params={"file_id": file_id},
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}"},
                )
                response.raise_for_status()
                body = response.json()
        except Exception:
            return None
        file_info = body.get("file") or {}
        return file_info.get("download_url")

    async def upload_voice_file(self, file_data: bytes, filename: str, purpose: str) -> dict:
        settings = get_settings()
        if not settings.minimax_api_key or settings.minimax_api_key == "replace_me":
            raise ProviderNotConfigured("MiniMax API key is missing", "Set MINIMAX_API_KEY")

        if purpose not in ("voice_clone", "prompt_audio"):
            raise ProviderError("Invalid purpose", f"purpose must be 'voice_clone' or 'prompt_audio', got '{purpose}'")

        url = settings.minimax_base_url.rstrip("/") + settings.minimax_file_upload_path
        try:
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}"},
                    data={"purpose": purpose},
                    files={"file": (filename, file_data)},
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise ProviderError("MiniMax file upload failed", str(exc)) from exc

        base_resp = body.get("base_resp") or {}
        if base_resp.get("status_code") not in (None, 0):
            raise ProviderError("MiniMax file upload failed", base_resp.get("status_msg"))

        file_info = body.get("file") or {}
        return {
            "file_id": file_info.get("file_id"),
            "filename": file_info.get("filename"),
            "purpose": file_info.get("purpose", purpose),
            "bytes": file_info.get("bytes"),
            "created_at": file_info.get("created_at"),
        }

    async def clone_voice(self, request: dict) -> dict:
        settings = get_settings()
        if not settings.minimax_api_key or settings.minimax_api_key == "replace_me":
            raise ProviderNotConfigured("MiniMax API key is missing", "Set MINIMAX_API_KEY")

        payload = {
            "file_id": request["file_id"],
            "voice_id": request["voice_id"],
        }
        for key in ("text", "model", "language_boost", "need_noise_reduction", "need_volume_normalization"):
            if key in request and request[key] is not None:
                payload[key] = request[key]

        prompt_file_id = request.get("prompt_file_id")
        prompt_text = request.get("prompt_text")
        if prompt_file_id is not None and prompt_text is not None:
            payload["clone_prompt"] = {"prompt_audio": prompt_file_id, "prompt_text": prompt_text}

        url = settings.minimax_base_url.rstrip("/") + settings.minimax_voice_clone_path
        try:
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise ProviderError("MiniMax voice clone failed", str(exc)) from exc

        base_resp = body.get("base_resp") or {}
        if base_resp.get("status_code") not in (None, 0):
            raise ProviderError("MiniMax voice clone failed", base_resp.get("status_msg"))

        input_sensitive = body.get("input_sensitive") or {}
        sensitive_type = input_sensitive.get("type")
        if sensitive_type is not None and sensitive_type != 0:
            raise ProviderError("内容安全检测未通过", f"input_sensitive.type={sensitive_type}")

        extra = body.get("extra_info") or {}
        return {
            "voice_id": body.get("voice_id"),
            "demo_audio_url": body.get("demo_audio"),
            "duration_ms": extra.get("audio_length"),
            "usage_characters": extra.get("usage_characters"),
        }

    async def design_voice(self, prompt: str, preview_text: str, voice_id: str | None = None) -> dict:
        settings = get_settings()
        if not settings.minimax_api_key or settings.minimax_api_key == "replace_me":
            raise ProviderNotConfigured("MiniMax API key is missing", "Set MINIMAX_API_KEY")

        payload: dict = {"prompt": prompt, "preview_text": preview_text}
        if voice_id is not None:
            payload["voice_id"] = voice_id

        url = settings.minimax_base_url.rstrip("/") + settings.minimax_voice_design_path
        try:
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise ProviderError("MiniMax voice design failed", str(exc)) from exc

        base_resp = body.get("base_resp") or {}
        if base_resp.get("status_code") not in (None, 0):
            raise ProviderError("MiniMax voice design failed", base_resp.get("status_msg"))

        return {
            "voice_id": body.get("voice_id"),
            "trial_audio_hex": body.get("trial_audio"),
        }

    async def delete_voice(self, provider_voice_id: str, voice_type: str = "voice_cloning") -> dict:
        settings = get_settings()
        if not settings.minimax_api_key or settings.minimax_api_key == "replace_me":
            raise ProviderNotConfigured("MiniMax API key is missing", "Set MINIMAX_API_KEY")

        payload = {"voice_type": voice_type, "voice_id": provider_voice_id}
        url = settings.minimax_base_url.rstrip("/") + settings.minimax_delete_voice_path
        try:
            async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()
        except Exception as exc:
            raise ProviderError("MiniMax delete voice failed", str(exc)) from exc

        base_resp = body.get("base_resp") or {}
        if base_resp.get("status_code") not in (None, 0):
            raise ProviderError("MiniMax delete voice failed", base_resp.get("status_msg"))

        return {"voice_id": provider_voice_id, "deleted": True}
