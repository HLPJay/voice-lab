"""Xiaomi MiMo Chat TTS Adapter.

Uses OpenAI Chat Completions format for TTS.
Reference: https://platform.xiaomimimo.com/docs/zh-CN/usage-guide/speech-synthesis-v2.5

B1 scope:
- render_sync with mimo-v2.5-tts model
- static preset voice list via list_voices
- wav non-streaming output
- base64 audio parsing
- mock transport for testing

Not in B1:
- render_stream
- voice design
- voice cloning
- async tasks
"""

from __future__ import annotations

import base64
import os
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
    """Xiaomi MiMo TTS adapter using OpenAI Chat Completions format.

    Supports:
    - sync TTS with mimo-v2.5-tts model
    - static preset voice list
    - wav output format (non-streaming)

    B1 does NOT support:
    - streaming (stream=true)
    - voice design (mimo-v2.5-tts-voicedesign model)
    - voice cloning (mimo-v2.5-tts-voiceclone model)
    """

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

        client = await self._get_client()
        try:
            response = await client.request(
                method,
                url,
                headers={"api-key": api_key},
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
        """Render TTS using Xiaomi MiMo OpenAI Chat Completions format.

        Request format:
        {
            "model": "mimo-v2.5-tts",
            "messages": [
                {"role": "assistant", "content": "text to synthesize"}
            ],
            "audio": {"format": "wav", "voice": "voice_id"}
        }

        Response format:
        {
            "choices": [{
                "message": {
                    "audio": {"data": "<base64>", "format": "wav"},
                    "content": ""
                }
            }]
        }

        Config hierarchy for model:
        1. plan.model
        2. ProviderConfig.default_model
        3. AdapterConfig.default_model
        4. Hardcoded fallback
        """
        # Determine model using config hierarchy
        model = self._get_model(plan)

        # Determine voice
        voice = plan.provider_voice_id or "mimo_default"

        # Build messages: the text to synthesize goes in role=assistant
        messages = [
            {"role": "assistant", "content": plan.processed_text or plan.text},
        ]

        # Xiaomi MiMo supports wav and pcm16; we default to wav
        audio_format = "wav"

        # Build request payload
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
        """Xiaomi MiMo voice design not supported in this adapter (B1).

        Use mimo-v2.5-tts-voicedesign model with OpenAI-compatible adapter for voice design.
        """
        raise ProviderError(
            "Voice design not supported in xiaomi_mimo_chat_tts adapter (B1)",
            "Use mimo-v2.5-tts-voicedesign model with OpenAI-compatible adapter",
        )

    async def create_async_task(self, plan: RenderPlan) -> dict:
        """Xiaomi MiMo API is synchronous - no async task support in B1."""
        raise ProviderError(
            "Async tasks not supported",
            "Xiaomi MiMo TTS API is synchronous in B1",
        )

    async def query_async_task(self, provider_task_id: str) -> dict:
        """Xiaomi MiMo API is synchronous - no async task support in B1."""
        raise ProviderError(
            "Async tasks not supported",
            "Xiaomi MiMo TTS API is synchronous in B1",
        )

    async def upload_voice_file(self, file_data: bytes, filename: str, purpose: str) -> dict:
        """Xiaomi MiMo voice cloning not supported in this adapter (B1)."""
        raise ProviderError(
            "Voice file upload not supported in xiaomi_mimo_chat_tts adapter (B1)",
            "Use mimo-v2.5-tts-voiceclone model with OpenAI-compatible adapter",
        )

    async def clone_voice(self, request: dict) -> dict:
        """Xiaomi MiMo voice cloning not supported in this adapter (B1)."""
        raise ProviderError(
            "Voice cloning not supported in xiaomi_mimo_chat_tts adapter (B1)",
            "Use mimo-v2.5-tts-voiceclone model with OpenAI-compatible adapter",
        )
