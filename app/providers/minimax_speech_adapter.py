import asyncio
import binascii
import json as _json
import re
import time
from pathlib import Path
from typing import AsyncGenerator

import httpx
import websockets

from app.core.config import get_settings
from app.core.context import get_job_id, get_request_id
from app.core.errors import ProviderError, ProviderNotConfigured
from app.core.logging import get_logger
from app.core.time import utc_now_iso
from app.domain.enums import ProviderVoiceStatus
from app.domain.render_plan import RenderPlan
from app.domain.schemas import ProviderVoiceRead
from app.models.provider_call_log import ProviderCallLog
from app.providers.base import AsyncTaskResult, AsyncTaskStatus, ProviderRenderResult, SpeechProvider, StreamAudioChunk
from app.utils.audio import estimate_duration_ms
from app.utils.files import storage_path
from app.utils.id_generator import new_id

_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]+$")
_provider_logger = get_logger("provider.minimax")
_retry_logger = get_logger("retry")

# Shared httpx client for connection reuse
_shared_http_client: httpx.AsyncClient | None = None


def _get_shared_http_client(timeout: int) -> httpx.AsyncClient:
    global _shared_http_client
    if _shared_http_client is None:
        _shared_http_client = httpx.AsyncClient(timeout=timeout, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))
    return _shared_http_client


class MiniMaxSpeechAdapter(SpeechProvider):
    provider_name = "minimax"

    @property
    def _base_url(self) -> str:
        return get_settings().minimax_base_url.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        timeout: int | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request to MiniMax API with automatic retry.

        Retries on httpx.TimeoutException, httpx.NetworkError, and 502/503/504
        responses with exponential backoff. Logs every attempt (provider_request)
        but only the final result (provider_response / provider_error). Audit log
        is written only once for the final result.
        """
        settings = get_settings()
        url = f"{self._base_url}{path}"
        request_timeout = timeout if timeout is not None else settings.minimax_timeout_seconds
        max_attempts = settings.provider_retry_max_attempts
        backoff_base = settings.provider_retry_backoff_base
        retryable_exceptions = (httpx.TimeoutException, httpx.NetworkError)
        retryable_status_codes = (502, 503, 504)

        overall_start = time.monotonic()
        response: httpx.Response | None = None
        final_response: httpx.Response | None = None
        final_error: Exception | None = None
        final_status_code: int | None = None
        final_error_type: str | None = None
        final_error_message: str | None = None

        for attempt in range(1, max_attempts + 1):
            attempt_start = time.monotonic()
            response = None

            _provider_logger.debug(
                "provider_request",
                extra={
                    "provider": self.provider_name,
                    "method": method,
                    "path": path,
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                },
            )

            try:
                client = _get_shared_http_client(request_timeout)
                response = await client.request(
                    method,
                    url,
                    headers={"Authorization": f"Bearer {settings.minimax_api_key}"},
                    **kwargs,
                )
                attempt_duration_ms = round((time.monotonic() - attempt_start) * 1000)

                if response.status_code in retryable_status_codes and attempt < max_attempts:
                    wait_seconds = backoff_base * (2 ** (attempt - 1))
                    _retry_logger.warning(
                        "retry_status_code",
                        extra={
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "status_code": response.status_code,
                            "wait_seconds": wait_seconds,
                            "path": path,
                            "method": method,
                        },
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                # Final response (success or non-retryable status)
                final_response = response
                final_status_code = response.status_code
                total_duration_ms = round((time.monotonic() - overall_start) * 1000)

                _provider_logger.info(
                    "provider_response",
                    extra={
                        "provider": self.provider_name,
                        "method": method,
                        "path": path,
                        "status_code": final_status_code,
                        "duration_ms": total_duration_ms,
                        "attempts": attempt,
                    },
                )
                self._save_call_log(
                    method=method,
                    path=path,
                    status_code=final_status_code,
                    duration_ms=total_duration_ms,
                    error_type=None,
                    error_message=None,
                )
                return response

            except retryable_exceptions as exc:
                attempt_duration_ms = round((time.monotonic() - attempt_start) * 1000)
                final_error = exc
                final_error_type = type(exc).__name__
                final_error_message = str(exc)

                if attempt < max_attempts:
                    wait_seconds = backoff_base * (2 ** (attempt - 1))
                    _retry_logger.warning(
                        "retry_exception",
                        extra={
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "error_type": final_error_type,
                            "error_message": final_error_message[:200],
                            "wait_seconds": wait_seconds,
                            "path": path,
                            "method": method,
                        },
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                # Exhausted retries
                total_duration_ms = round((time.monotonic() - overall_start) * 1000)
                _provider_logger.error(
                    "provider_error",
                    extra={
                        "provider": self.provider_name,
                        "method": method,
                        "path": path,
                        "error_type": final_error_type,
                        "error_message": final_error_message,
                        "duration_ms": total_duration_ms,
                        "attempts": attempt,
                    },
                )
                self._save_call_log(
                    method=method,
                    path=path,
                    status_code=None,
                    duration_ms=total_duration_ms,
                    error_type=final_error_type,
                    error_message=final_error_message,
                )
                raise

            except Exception as exc:
                # Non-retryable exception — fail immediately
                total_duration_ms = round((time.monotonic() - overall_start) * 1000)
                error_type = type(exc).__name__
                error_message = str(exc)
                _provider_logger.error(
                    "provider_error",
                    extra={
                        "provider": self.provider_name,
                        "method": method,
                        "path": path,
                        "error_type": error_type,
                        "error_message": error_message,
                        "duration_ms": total_duration_ms,
                        "attempts": 1,
                    },
                )
                self._save_call_log(
                    method=method,
                    path=path,
                    status_code=None,
                    duration_ms=total_duration_ms,
                    error_type=error_type,
                    error_message=error_message,
                )
                raise

    def _save_call_log(
        self,
        *,
        method: str,
        path: str,
        status_code: int | None,
        duration_ms: int,
        error_type: str | None,
        error_message: str | None,
    ) -> None:
        """Write audit record to provider_call_logs. Failures are logged but never raised."""
        try:
            from app.core.database import get_engine
            from sqlmodel import Session

            log_entry = ProviderCallLog(
                id=new_id("calllog"),
                request_id=get_request_id() or None,
                job_id=get_job_id() or None,
                provider=self.provider_name,
                api_path=path,
                method=method,
                status_code=status_code,
                duration_ms=duration_ms,
                error_type=error_type,
                error_message=(error_message or "")[:500],
                created_at=utc_now_iso(),
            )
            with Session(get_engine()) as session:
                session.add(log_entry)
                session.commit()
        except Exception as exc:
            _provider_logger.warning("call_log_save_failed", extra={"error": str(exc)})

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

        try:
            response = await self._request("POST", "/v1/get_voice", json={"voice_type": voice_type})
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
        try:
            response = await self._request("POST", settings.minimax_t2a_path, json=payload)
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

        duration_ms = extra.get("audio_length") or extra.get("duration_ms") or estimate_duration_ms(plan.processed_text)
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
        try:
            response = await self._request("POST", settings.minimax_async_t2a_path, json=payload)
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

        try:
            response = await self._request("GET", settings.minimax_async_query_path, params={"task_id": provider_task_id})
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
                file_url = await self._retrieve_file_url(file_id)

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

    async def _retrieve_file_url(self, file_id: int) -> str | None:
        try:
            response = await self._request("GET", "/v1/files/retrieve", params={"file_id": file_id})
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

        try:
            response = await self._request(
                "POST",
                settings.minimax_file_upload_path,
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

        try:
            response = await self._request("POST", settings.minimax_voice_clone_path, json=payload)
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

        try:
            response = await self._request("POST", settings.minimax_voice_design_path, json=payload)
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
        try:
            response = await self._request("POST", settings.minimax_delete_voice_path, json=payload)
            response.raise_for_status()
            body = response.json()
        except Exception as exc:
            raise ProviderError("MiniMax delete voice failed", str(exc)) from exc

        base_resp = body.get("base_resp") or {}
        if base_resp.get("status_code") not in (None, 0):
            raise ProviderError("MiniMax delete voice failed", base_resp.get("status_msg"))

        return {"voice_id": provider_voice_id, "deleted": True}

    async def render_stream(self, plan: RenderPlan) -> AsyncGenerator[StreamAudioChunk, None]:
        """Connect to MiniMax WebSocket and stream audio chunks."""
        settings = get_settings()
        if not settings.minimax_api_key or settings.minimax_api_key == "replace_me":
            raise ProviderNotConfigured("MiniMax API key is missing", "Set MINIMAX_API_KEY")

        ws_url = settings.minimax_ws_url
        headers = {"Authorization": f"Bearer {settings.minimax_api_key}"}
        voice_params = plan.voice_params or {}

        voice_setting: dict = {
            "voice_id": plan.provider_voice_id,
            "speed": voice_params.get("speed", 1.0),
            "vol": voice_params.get("vol", 1.0),
            "pitch": voice_params.get("pitch", 0),
        }
        if voice_params.get("emotion"):
            voice_setting["emotion"] = voice_params["emotion"]

        task_start_msg = {
            "event": "task_start",
            "model": settings.minimax_ws_model,
            "voice_setting": voice_setting,
            "audio_setting": {
                "format": plan.audio_params.get("format", "mp3"),
                "sample_rate": plan.audio_params.get("sample_rate", 32000),
                "bitrate": plan.audio_params.get("bitrate", 128000),
                "channel": plan.audio_params.get("channel", 1),
            },
        }

        _provider_logger.info(
            "ws_connect",
            extra={"provider": "minimax", "url": ws_url, "model": settings.minimax_ws_model},
        )

        start_time = time.monotonic()
        chunk_index = 0

        try:
            async with websockets.connect(
                ws_url,
                additional_headers=headers,
                close_timeout=10,
                open_timeout=settings.minimax_ws_timeout_seconds,
            ) as ws:
                # Wrap recv with timeout to avoid hanging indefinitely
                recv_timeout = settings.minimax_ws_timeout_seconds

                msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=recv_timeout))
                if msg.get("event") != "connected_success":
                    raise ProviderError("WebSocket connection failed", str(msg))

                await ws.send(_json.dumps(task_start_msg))

                msg = _json.loads(await asyncio.wait_for(ws.recv(), timeout=recv_timeout))
                if msg.get("event") == "task_failed":
                    base_resp = msg.get("base_resp", {})
                    status_msg = base_resp.get("status_msg", str(msg))
                    _provider_logger.error("ws_task_start_failed status_msg=%s base_resp=%s", status_msg, base_resp)
                    raise ProviderError("WebSocket task_start failed", status_msg)

                await ws.send(_json.dumps({"event": "task_continue", "text": plan.processed_text}))
                await ws.send(_json.dumps({"event": "task_finish"}))

                async for raw_msg in ws:
                    msg = _json.loads(raw_msg)
                    event = msg.get("event")

                    if event == "task_continued":
                        data = msg.get("data", {})
                        audio_hex = data.get("audio", "")
                        extra_info = data.get("extra_info", {})

                        if audio_hex:
                            audio_bytes = binascii.unhexlify(audio_hex)
                            yield StreamAudioChunk(
                                chunk_index=chunk_index,
                                audio_data=audio_bytes,
                                duration_ms=extra_info.get("audio_length"),
                                audio_size=extra_info.get("audio_size"),
                                is_final=msg.get("is_final", False),
                                usage_characters=extra_info.get("usage_characters"),
                                trace_id=msg.get("trace_id"),
                                metadata=extra_info,
                            )
                            chunk_index += 1

                    elif event == "task_finished":
                        break

                    elif event == "task_failed":
                        base_resp = msg.get("base_resp", {})
                        status_msg = base_resp.get("status_msg", str(msg))
                        _provider_logger.error("ws_task_failed status_msg=%s base_resp=%s", status_msg, base_resp)
                        raise ProviderError("WebSocket task failed", status_msg)

            duration_ms = round((time.monotonic() - start_time) * 1000)
            _provider_logger.info(
                "ws_complete",
                extra={
                    "provider": "minimax",
                    "chunks": chunk_index,
                    "duration_ms": duration_ms,
                },
            )
            self._save_call_log(
                method="WS",
                path=settings.minimax_ws_url,
                status_code=200,
                duration_ms=duration_ms,
            )

        except ProviderError:
            raise
        except Exception as exc:
            duration_ms = round((time.monotonic() - start_time) * 1000)
            _provider_logger.error(
                "ws_error",
                extra={
                    "provider": "minimax",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc)[:200],
                    "duration_ms": duration_ms,
                },
            )
            self._save_call_log(
                method="WS",
                path=settings.minimax_ws_url,
                status_code=None,
                duration_ms=duration_ms,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise ProviderError("MiniMax WebSocket failed", str(exc)) from exc
