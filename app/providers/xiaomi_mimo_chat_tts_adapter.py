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
from typing import Any

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

_provider_logger = get_logger("provider.xiaomi_mimo_chat_tts")

# Default base URL for Xiaomi MiMo API
DEFAULT_BASE_URL = "https://api.xiaomimimo.com"
DEFAULT_MODEL = "mimo-v2.5-tts"
DEFAULT_TIMEOUT_SECONDS = 120


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

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        """Initialize the adapter.

        Args:
            http_client: Optional httpx.AsyncClient for making HTTP requests.
                         If not provided, a default client is used.
        """
        self._http_client = http_client
        self._owns_client = http_client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS)
        return self._http_client

    async def _close_client(self) -> None:
        """Close the HTTP client if we own it."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def _get_api_key(self) -> str:
        """Get the Xiaomi MiMo API key from environment.

        Raises:
            ProviderNotConfigured: If the API key is not set.
        """
        api_key = os.environ.get("MIMO_API_KEY")
        if not api_key or api_key == "replace_me":
            raise ProviderNotConfigured(
                "Xiaomi MiMo API key is missing",
                "Set MIMO_API_KEY environment variable",
            )
        return api_key

    def _get_base_url(self) -> str:
        """Get the Xiaomi MiMo base URL from environment or default."""
        return os.environ.get("XIAOMI_MIMO_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        timeout: int | None = None,
        **kwargs,
    ) -> httpx.Response:
        """Make an HTTP request to Xiaomi MiMo API."""
        base_url = self._get_base_url()
        api_key = self._get_api_key()
        url = f"{base_url}{path}"
        request_timeout = timeout or DEFAULT_TIMEOUT_SECONDS

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
        """
        # Determine model
        model = plan.model or DEFAULT_MODEL

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
            response = await self._request("POST", "/v1/chat/completions", json=payload)
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

        These are static preset voices, not fetched from API.
        """
        preset_voices = [
            {
                "id": "mimo_default",
                "name": "MiMo-默认",
                "language": "zh",
                "gender": "neutral",
                "description": "默认音色",
            },
            {
                "id": "冰糖",
                "name": "冰糖",
                "language": "zh",
                "gender": "female",
                "description": "中文女性音色",
            },
            {
                "id": "茉莉",
                "name": "茉莉",
                "language": "zh",
                "gender": "female",
                "description": "中文女性音色",
            },
            {
                "id": "苏打",
                "name": "苏打",
                "language": "zh",
                "gender": "male",
                "description": "中文男性音色",
            },
            {
                "id": "白桦",
                "name": "白桦",
                "language": "zh",
                "gender": "male",
                "description": "中文男性音色",
            },
            {
                "id": "Mia",
                "name": "Mia",
                "language": "en",
                "gender": "female",
                "description": "English female voice",
            },
            {
                "id": "Chloe",
                "name": "Chloe",
                "language": "en",
                "gender": "female",
                "description": "English female voice",
            },
            {
                "id": "Milo",
                "name": "Milo",
                "language": "en",
                "gender": "male",
                "description": "English male voice",
            },
            {
                "id": "Dean",
                "name": "Dean",
                "language": "en",
                "gender": "male",
                "description": "English male voice",
            },
        ]

        voices = []
        for v in preset_voices:
            voices.append(
                ProviderVoiceRead(
                    id=f"xiaomi_mimo_{v['id']}",
                    provider=self.provider_name,
                    provider_voice_id=v["id"],
                    voice_type="system",
                    name=v["name"],
                    description=v.get("description"),
                    language=v.get("language"),
                    gender=v.get("gender"),
                    status=ProviderVoiceStatus.available,
                    metadata={"voice_id": v["id"]},
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
