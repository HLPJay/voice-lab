import binascii
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.errors import ProviderError, ProviderNotConfigured
from app.domain.render_plan import RenderPlan
from app.domain.schemas import ProviderVoiceRead
from app.providers.base import ProviderRenderResult, SpeechProvider
from app.utils.audio import estimate_duration_ms
from app.utils.files import storage_path
from app.utils.id_generator import new_id


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
                        status="available",
                        provider_created_time=item.get("created_time"),
                        metadata={"raw": item},
                    )
                )
        return voices

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
        audio_hex = data.get("audio")
        audio_url = data.get("audio_url") or data.get("url")
        fmt = plan.audio_params.get("format", "mp3")
        audio_path = storage_path("audio", f"{new_id('audio_file')}.{fmt}")
        try:
            if audio_hex:
                audio_path.write_bytes(binascii.unhexlify(audio_hex))
            elif audio_url:
                async with httpx.AsyncClient(timeout=settings.minimax_timeout_seconds) as client:
                    audio_response = await client.get(audio_url)
                    audio_response.raise_for_status()
                    audio_path.write_bytes(audio_response.content)
            else:
                raise ValueError("MiniMax response did not contain audio hex or url")
        except Exception as exc:
            raise ProviderError("MiniMax audio save failed", str(exc)) from exc

        extra = body.get("extra_info") or {}
        subtitle_info = data.get("subtitle") or data.get("subtitle_file") or {}
        timeline = subtitle_info if isinstance(subtitle_info, list) else []
        duration_ms = extra.get("audio_length") or extra.get("duration_ms") or estimate_duration_ms(plan.text)
        return ProviderRenderResult(
            audio_path=str(Path(audio_path)),
            duration_ms=duration_ms,
            usage_characters=extra.get("usage_characters") or len(plan.text),
            trace_id=trace_id,
            response_json=body,
            timeline=timeline,
            metadata={"extra_info": extra},
        )
