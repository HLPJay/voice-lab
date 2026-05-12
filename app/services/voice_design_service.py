import binascii

from sqlmodel import Session

from app.core.errors import ProviderError, ValidationError
from app.core.logging import get_logger
from app.domain.enums import ProviderVoiceStatus
from app.domain.schemas import VoiceDesignRequest, VoiceDesignResponse
from app.providers.registry import get_provider
from app.repositories.provider_voice_repo import upsert_provider_voice
from app.utils.files import storage_path


def _require_cost_confirm(provider: str, confirm_cost: bool) -> None:
    """Raise ValidationError if minimax high-risk operation has no cost confirmation."""
    if provider == "minimax" and not confirm_cost:
        raise ValidationError(
            "需要确认成本后才能执行声音设计",
            "voice_design requires confirm_cost=true for minimax provider",
        )


class VoiceDesignService:
    def __init__(self):
        self.logger = get_logger("voice_design")

    async def design_voice(
        self,
        session: Session,
        provider: str,
        request: VoiceDesignRequest,
    ) -> VoiceDesignResponse:
        _require_cost_confirm(provider, request.confirm_cost)

        adapter = get_provider(provider)
        result = await adapter.design_voice(
            request.prompt, request.preview_text, request.voice_id
        )

        voice_id = result.get("voice_id")
        if not voice_id:
            raise ProviderError(
                "Voice design returned empty voice_id",
                str(result),
            )

        trial_audio_url = None
        trial_audio_hex = result.get("trial_audio_hex")

        if trial_audio_hex:
            audio_path = storage_path("audio", f"{voice_id}_trial.mp3")
            audio_path.write_bytes(binascii.unhexlify(trial_audio_hex))
            trial_audio_url = f"/api/voice/assets/trial/{voice_id}/download"

        upsert_provider_voice(
            session,
            provider=provider,
            provider_voice_id=voice_id,
            voice_type="voice_generation",
            name=voice_id,
            description=request.prompt,
            status=ProviderVoiceStatus.available,
            metadata={
                "source": "voice_design",
                "prompt": request.prompt,
                "has_trial_audio": bool(trial_audio_hex or trial_audio_url),
            },
        )

        self.logger.info(
            "design_voice provider=%s voice_id=%s", provider, voice_id
        )

        return VoiceDesignResponse(
            voice_id=voice_id,
            trial_audio_url=trial_audio_url,
            trial_audio_hex=trial_audio_hex,
            message=result.get("message", "设计成功"),
        )