"""Xiaomi MiMo Chat TTS Adapter.

Uses OpenAI Chat Completions format for TTS.
Reference: https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5

Supports:
- render_sync with mimo-v2.5-tts model
- voice design with mimo-v2.5-tts-voicedesign model
- voice clone with mimo-v2.5-tts-voiceclone model (base64 data URI, no file upload)
- static preset voice list via list_voices
- wav/pcm16 output
- direct HTTP calls use api-key header (works for both sk- and tp- prefix keys)
- dual-prefix auth routing is reserved for future work, not implemented in this stage
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

from app.core.errors import ProviderError, ProviderNotConfigured
from app.core.logging import get_logger
from app.domain.enums import ProviderVoiceStatus
from app.domain.render_plan import RenderPlan
from app.domain.schemas import ProviderVoiceRead
from app.providers.base import ProviderRenderResult, SpeechProvider
from app.utils.audio import estimate_duration_ms
from app.utils.files import storage_path
from app.utils.id_generator import new_id

if TYPE_CHECKING:
    from app.domain.adapter_config import AdapterConfig
    from app.domain.provider_config import ProviderConfig

_provider_logger = get_logger("provider.xiaomi_mimo_chat_tts")

# Hardcoded fallback values (lowest priority in config hierarchy)
_FALLBACK_BASE_URL = "https://api.xiaomimimo.com"
_FALLBACK_MODEL = "mimo-v2.5-tts"
_FALLBACK_TIMEOUT_SECONDS = 120
_FALLBACK_ENDPOINT = "/v1/chat/completions"


class XiaomiMiMoChatTTSAdapter(SpeechProvider):
    """Xiaomi MiMo TTS adapter using OpenAI Chat Completions format."""

    provider_name = "xiaomi_mimo"

    def __init__(
        self,
        provider_config: "ProviderConfig | None" = None,
        adapter_config: "AdapterConfig | None" = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(provider_config=provider_config, adapter_config=adapter_config)
        self._http_client = http_client
        self._owns_client = http_client is None

    def _get_provider_config(self) -> "ProviderConfig | None":
        """Get provider config, loading from registry if not injected."""
        if self._provider_config is not None:
            return self._provider_config
        from app.config.provider_config_loader import get_provider_config
        return get_provider_config(self.provider_name)

    def _get_adapter_config(self) -> "AdapterConfig | None":
        """Get adapter config, loading from registry if not injected."""
        if self._adapter_config is not None:
            return self._adapter_config
        from app.config.adapter_config_loader import get_adapter_config
        return get_adapter_config("xiaomi_mimo_chat_tts")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            timeout = self._get_timeout()
            self._http_client = httpx.AsyncClient(timeout=timeout)
        return self._http_client

    async def _close_client(self) -> None:
        """Close the HTTP client if we own it."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def _get_api_key(self) -> str:
        """Get the Xiaomi MiMo API key from ProviderConfig.

        Config hierarchy:
        1. ProviderConfig.resolved_api_key (from api_key_env, via .env or os.environ)

        Raises:
            ProviderNotConfigured: If the API key is not set or "replace_me".
        """
        provider_config = self._get_provider_config()
        if provider_config is None:
            raise ProviderNotConfigured(
                "Xiaomi MiMo provider config not found",
                "Ensure xiaomi_mimo is defined in config/providers.yaml",
            )

        api_key = provider_config.resolved_api_key
        if not api_key or api_key == "replace_me":
            env_name = provider_config.api_key_env or "MIMO_API_KEY"
            raise ProviderNotConfigured(
                "Xiaomi MiMo API key is missing",
                f"Set {env_name} environment variable",
            )
        return api_key

    def _get_base_url(self) -> str:
        """Get the Xiaomi MiMo base URL from config hierarchy.

        Config hierarchy:
        1. ProviderConfig.resolved_base_url (from base_url_env or base_url)
        2. AdapterConfig.default_base_url
        3. Hardcoded fallback
        """
        provider_config = self._get_provider_config()
        adapter_config = self._get_adapter_config()

        # Try ProviderConfig first
        if provider_config is not None:
            base_url = provider_config.resolved_base_url
            if base_url:
                return base_url.rstrip("/")

        # Try AdapterConfig
        if adapter_config is not None and adapter_config.default_base_url:
            return adapter_config.default_base_url.rstrip("/")

        # Fallback
        return _FALLBACK_BASE_URL.rstrip("/")

    def _get_endpoint(self) -> str:
        """Get the TTS endpoint from config hierarchy.

        Config hierarchy:
        1. ProviderConfig.endpoints.tts
        2. AdapterConfig.endpoints.tts
        3. Hardcoded fallback
        """
        provider_config = self._get_provider_config()
        adapter_config = self._get_adapter_config()

        # Try ProviderConfig first
        if provider_config is not None and provider_config.endpoints:
            endpoint = provider_config.endpoints.tts
            if endpoint:
                return endpoint

        # Try AdapterConfig
        if adapter_config is not None and adapter_config.endpoints:
            endpoint = adapter_config.endpoints.tts
            if endpoint:
                return endpoint

        # Fallback
        return _FALLBACK_ENDPOINT

    def _get_model(self, plan: RenderPlan) -> str:
        """Get the model from config hierarchy.

        Config hierarchy:
        1. plan.model
        2. ProviderConfig.default_model
        3. AdapterConfig.default_model
        4. Hardcoded fallback
        """
        adapter_config = self._get_adapter_config()

        # plan.model takes precedence
        if plan.model:
            return plan.model

        # Try ProviderConfig
        provider_config = self._get_provider_config()
        if provider_config is not None and provider_config.default_model:
            return provider_config.default_model

        # Try AdapterConfig
        if adapter_config is not None and adapter_config.default_model:
            return adapter_config.default_model

        # Fallback
        return _FALLBACK_MODEL

    def _get_timeout(self) -> int:
        """Get the timeout from config hierarchy.

        Config hierarchy:
        1. ProviderConfig.timeout_seconds (if added in future)
        2. AdapterConfig.default_timeout_seconds
        3. Hardcoded fallback
        """
        adapter_config = self._get_adapter_config()

        if adapter_config is not None and adapter_config.default_timeout_seconds:
            return adapter_config.default_timeout_seconds

        return _FALLBACK_TIMEOUT_SECONDS

    async def _request(
        self,
        method: str,
        path: str | None = None,
        *,
        timeout: int | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request to Xiaomi MiMo API.

        Args:
            method: HTTP method.
            path: API path. If None, uses _get_endpoint().
            timeout: Request timeout override. If None, uses _get_timeout().
            **kwargs: Additional arguments passed to httpx client.
        """
        base_url = self._get_base_url()
        api_key = self._get_api_key()
        if path is None:
            path = self._get_endpoint()
        url = f"{base_url}{path}"
        request_timeout = timeout if timeout is not None else self._get_timeout()

        _provider_logger.debug(
            "provider_request",
            extra={
                "provider": self.provider_name,
                "method": method,
                "path": path,
            },
        )

        # Auth: api-key header works for both sk- and tp- prefix keys
        # OpenAI SDK compat (Authorization: Bearer) also works, but api-key is
        # the officially documented method for direct HTTP calls.
        headers = {"api-key": api_key}

        client = await self._get_client()
        try:
            response = await client.request(
                method,
                url,
                headers=headers,
                timeout=request_timeout,
                **kwargs,
            )

            duration_ms = 0
            _provider_logger.info(
                "provider_response",
                extra={
                    "provider": self.provider_name,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            return response
        except httpx.TimeoutException as exc:
            _provider_logger.error(
                "provider_error",
                extra={
                    "provider": self.provider_name,
                    "method": method,
                    "path": path,
                    "error_type": "TimeoutException",
                    "error_message": str(exc),
                },
            )
            raise ProviderError("Xiaomi MiMo request timeout", str(exc)) from exc
        except httpx.NetworkError as exc:
            _provider_logger.error(
                "provider_error",
                extra={
                    "provider": self.provider_name,
                    "method": method,
                    "path": path,
                    "error_type": "NetworkError",
                    "error_message": str(exc),
                },
            )
            raise ProviderError("Xiaomi MiMo network error", str(exc)) from exc

    async def render_sync(self, plan: RenderPlan) -> ProviderRenderResult:
        """Render TTS using Xiaomi MiMo Chat Completions format.

        Per official docs, message format:
        - user message (optional): style/emotion instructions
        - assistant message (required): text to synthesize
        """
        model = self._get_model(plan)
        voice = plan.provider_voice_id or "mimo_default"

        messages: list[dict[str, str]] = []
        # Optional user message for style/emotion control
        style_instruction = plan.voice_params.get("emotion") or plan.voice_params.get("style")
        if style_instruction:
            messages.append({"role": "user", "content": str(style_instruction)})
        messages.append({"role": "assistant", "content": plan.processed_text or plan.text})

        audio_format = "wav"

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "audio": {
                "format": audio_format,
                "voice": voice,
            },
        }

        try:
            # Use _get_endpoint() by default (no path argument)
            response = await self._request("POST", json=payload)
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            error_detail = exc.response.text
            _provider_logger.error(
                "tts_http_error",
                extra={
                    "status_code": exc.response.status_code,
                    "response": error_detail[:500],
                },
            )
            raise ProviderError(
                "Xiaomi MiMo TTS HTTP error",
                f"status={exc.response.status_code}, detail={error_detail[:200]}",
            ) from exc
        except ProviderNotConfigured:
            raise  # Re-raise without wrapping
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("Xiaomi MiMo TTS request failed", str(exc)) from exc

        # Parse response
        choices = body.get("choices", [])
        if not choices:
            raise ProviderError(
                "Xiaomi MiMo TTS response missing choices",
                f"response={body}",
            )

        message = choices[0].get("message", {})
        audio_data = message.get("audio", {}).get("data")
        returned_format = message.get("audio", {}).get("format", audio_format)

        if not audio_data:
            raise ProviderError(
                "Xiaomi MiMo TTS response missing audio data",
                f"message={message}",
            )

        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as exc:
            raise ProviderError(
                "Xiaomi MiMo TTS audio decode failed",
                f"error={str(exc)}",
            ) from exc

        if not audio_bytes:
            raise ProviderError(
                "Xiaomi MiMo TTS audio is empty",
                " decoded audio bytes are empty",
            )

        # Save audio to file
        audio_id = new_id("audio_file")
        ext = returned_format or "wav"
        audio_path = storage_path("audio", f"{audio_id}.{ext}")
        Path(audio_path).write_bytes(audio_bytes)

        # Estimate duration
        duration_ms = estimate_duration_ms(plan.processed_text or plan.text)

        # Usage from response (Xiaomi returns completion_tokens)
        usage = body.get("usage", {})
        usage_characters = usage.get("completion_tokens") or len(plan.text)

        return ProviderRenderResult(
            audio_path=str(audio_path),
            duration_ms=duration_ms,
            usage_characters=usage_characters,
            trace_id=body.get("id"),
            response_json=body,
            timeline=[],  # Xiaomi MiMo doesn't support subtitles
            metadata={
                "audio_format": returned_format,
                "provider": self.provider_name,
                "model": model,
                "voice": voice,
            },
        )

    async def list_voices(self, voice_type: str = "all") -> list[ProviderVoiceRead]:
        """Return static preset voice list for Xiaomi MiMo.

        Reference: https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5

        Voice source (config hierarchy):
        1. AdapterConfig.provider_voices.static_voices (if configured)
        2. Hardcoded fallback preset list

        These are static preset voices, not fetched from API.
        """
        # Default fallback preset voices (lowest priority)
        default_preset_voices = [
            {"voice_id": "mimo_default", "name": "MiMo-默认", "language": "zh", "gender": "neutral", "description": "默认音色"},
            {"voice_id": "冰糖", "name": "冰糖", "language": "zh", "gender": "female", "description": "中文女性音色"},
            {"voice_id": "茉莉", "name": "茉莉", "language": "zh", "gender": "female", "description": "中文女性音色"},
            {"voice_id": "苏打", "name": "苏打", "language": "zh", "gender": "male", "description": "中文男性音色"},
            {"voice_id": "白桦", "name": "白桦", "language": "zh", "gender": "male", "description": "中文男性音色"},
            {"voice_id": "Mia", "name": "Mia", "language": "en", "gender": "female", "description": "English female voice"},
            {"voice_id": "Chloe", "name": "Chloe", "language": "en", "gender": "female", "description": "English female voice"},
            {"voice_id": "Milo", "name": "Milo", "language": "en", "gender": "male", "description": "English male voice"},
            {"voice_id": "Dean", "name": "Dean", "language": "en", "gender": "male", "description": "English male voice"},
        ]

        # Try to get static voices from config first
        adapter_config = self._get_adapter_config()
        if adapter_config is not None and adapter_config.provider_voices is not None:
            static_voices = adapter_config.provider_voices.static_voices
            if static_voices:
                preset_voices = [
                    {
                        "voice_id": v.voice_id,
                        "name": v.name,
                        "language": v.language,
                        "gender": v.gender,
                        "description": v.description,
                    }
                    for v in static_voices
                ]
            else:
                preset_voices = default_preset_voices
        else:
            preset_voices = default_preset_voices

        voices = []
        for v in preset_voices:
            voices.append(
                ProviderVoiceRead(
                    id=f"xiaomi_mimo_{v['voice_id']}",
                    provider=self.provider_name,
                    provider_voice_id=v["voice_id"],
                    voice_type="system",
                    name=v["name"],
                    description=v.get("description"),
                    language=v.get("language"),
                    gender=v.get("gender"),
                    status=ProviderVoiceStatus.available,
                    metadata={"voice_id": v["voice_id"]},
                )
            )

        if voice_type != "all":
            voices = [v for v in voices if v.voice_type == voice_type]

        return voices

    async def delete_voice(self, provider_voice_id: str, voice_type: str = "voice_cloning") -> dict:
        """Xiaomi MiMo does not support voice deletion."""
        raise ProviderError(
            "Voice deletion not supported",
            "Xiaomi MiMo does not support delete_voice",
        )

    async def design_voice(self, prompt: str, preview_text: str, voice_id: str | None = None) -> dict:
        """Design a voice using MiMo voice design model.

        Per official docs:
        - model: mimo-v2.5-tts-voicedesign
        - user message (required): voice description prompt
        - assistant message: text to preview (optional if optimize_text_preview=true)
        - audio object: format + optimize_text_preview, NO voice field
        """
        model = "mimo-v2.5-tts-voicedesign"
        messages: list[dict[str, str]] = [
            {"role": "user", "content": prompt},
        ]
        if preview_text:
            messages.append({"role": "assistant", "content": preview_text})

        audio_obj: dict[str, Any] = {"format": "wav"}
        if not preview_text:
            audio_obj["optimize_text_preview"] = True

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "audio": audio_obj,
        }

        try:
            response = await self._request("POST", json=payload)
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                "Xiaomi MiMo voice design HTTP error",
                f"status={exc.response.status_code}, detail={exc.response.text[:200]}",
            ) from exc
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("Xiaomi MiMo voice design failed", str(exc)) from exc

        choices = body.get("choices", [])
        if not choices:
            raise ProviderError("Xiaomi MiMo voice design response missing choices", f"response={body}")

        message = choices[0].get("message", {})
        audio_data = message.get("audio", {}).get("data")

        result: dict[str, Any] = {
            "voice_id": voice_id or body.get("id"),
            "response_json": body,
        }

        if audio_data:
            audio_bytes = base64.b64decode(audio_data)
            audio_id = new_id("audio_file")
            audio_path = storage_path("audio", f"{audio_id}.wav")
            Path(audio_path).write_bytes(audio_bytes)
            result["trial_audio_path"] = str(audio_path)
            result["trial_audio_base64"] = audio_data

        return result

    async def create_async_task(self, plan: RenderPlan) -> dict:
        """Xiaomi MiMo API is synchronous only."""
        raise ProviderError(
            "Async tasks not supported",
            "Xiaomi MiMo TTS API is synchronous only",
        )

    async def query_async_task(self, provider_task_id: str) -> dict:
        """Xiaomi MiMo API is synchronous only."""
        raise ProviderError(
            "Async tasks not supported",
            "Xiaomi MiMo TTS API is synchronous only",
        )

    async def upload_voice_file(self, file_data: bytes, filename: str, purpose: str) -> dict:
        """MiMo voice clone doesn't need file upload — audio is passed inline as base64 data URI.

        This method stores the file locally and returns a reference for clone_voice to use.
        """
        audio_id = new_id("clone_ref")
        ext = Path(filename).suffix.lstrip(".") or "mp3"
        ref_path = storage_path("clone_ref", f"{audio_id}.{ext}")
        Path(ref_path).write_bytes(file_data)

        return {
            "file_id": audio_id,
            "file_path": str(ref_path),
            "file_size": len(file_data),
            "format": ext,
        }

    async def clone_voice(self, request: dict) -> dict:
        """Clone a voice using MiMo voice clone model.

        Uses model=mimo-v2.5-tts-voiceclone.
        Audio is passed as base64 data URI in audio.voice field.
        No separate file upload API needed.

        request keys:
        - file_id: local reference from upload_voice_file
        - voice_id: desired voice identifier (for naming)
        - preview_text: text to synthesize with cloned voice
        - file_path: (optional) path to reference audio file
        - audio_data: (optional) raw bytes of reference audio
        """
        model = "mimo-v2.5-tts-voiceclone"
        preview_text = request.get("preview_text", "你好，这是语音克隆的测试。")

        # Get reference audio as base64 data URI
        audio_data_uri = self._build_clone_audio_uri(request)

        messages = [
            {"role": "assistant", "content": preview_text},
        ]

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "audio": {
                "format": "wav",
                "voice": audio_data_uri,
            },
        }

        try:
            response = await self._request("POST", json=payload)
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(
                "Xiaomi MiMo voice clone HTTP error",
                f"status={exc.response.status_code}, detail={exc.response.text[:200]}",
            ) from exc
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("Xiaomi MiMo voice clone failed", str(exc)) from exc

        choices = body.get("choices", [])
        if not choices:
            raise ProviderError("Xiaomi MiMo voice clone response missing choices", f"response={body}")

        message = choices[0].get("message", {})
        audio_b64 = message.get("audio", {}).get("data")

        result: dict[str, Any] = {
            "voice_id": request.get("voice_id", body.get("id")),
            "response_json": body,
        }

        if audio_b64:
            audio_bytes = base64.b64decode(audio_b64)
            audio_id = new_id("audio_file")
            audio_path = storage_path("audio", f"{audio_id}.wav")
            Path(audio_path).write_bytes(audio_bytes)
            result["demo_audio_path"] = str(audio_path)
            result["demo_audio_url"] = str(audio_path)
            result["duration_ms"] = estimate_duration_ms(preview_text)

        return result

    @staticmethod
    def _ext_to_mime(ext: str) -> str:
        """Map file extension to MIME type for data URI (per MiMo docs)."""
        ext = ext.lower().lstrip(".")
        if ext in ("mp3", "mpeg"):
            return "audio/mpeg"
        return f"audio/{ext}"

    def _build_clone_audio_uri(self, request: dict) -> str:
        """Build base64 data URI from clone request audio source.

        Per MiMo docs: data:{MIME_TYPE};base64,{BASE64_AUDIO}
        Supported: audio/mpeg (mp3), audio/wav. Max 10MB base64.
        """
        if "audio_data" in request and request["audio_data"]:
            raw_bytes = request["audio_data"]
            fmt = request.get("format", "mp3")
            mime = self._ext_to_mime(fmt)
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            return f"data:{mime};base64,{b64}"

        file_path = request.get("file_path")
        if file_path:
            path = Path(file_path)
            if not path.exists():
                raise ProviderError("Clone reference audio not found", f"path={file_path}")
            raw_bytes = path.read_bytes()
            mime = self._ext_to_mime(path.suffix)
            b64 = base64.b64encode(raw_bytes).decode("ascii")
            return f"data:{mime};base64,{b64}"

        raise ProviderError(
            "Xiaomi MiMo voice clone missing audio",
            "Provide audio_data or file_path in clone request",
        )
