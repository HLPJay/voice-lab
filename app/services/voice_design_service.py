import binascii

from app.core.logging import get_logger
from app.domain.schemas import VoiceDesignRequest, VoiceDesignResponse
from app.providers.registry import get_provider
from app.utils.files import storage_path


class VoiceDesignService:
    def __init__(self):
        self.logger = get_logger("voice_design")

    async def design_voice(
        self,
        provider: str,
        request: VoiceDesignRequest,
    ) -> VoiceDesignResponse:
        adapter = get_provider(provider)
        result = await adapter.design_voice(
            request.prompt, request.preview_text, request.voice_id, request.model
        )

        trial_audio_url = None
        trial_audio_hex = result.get("trial_audio_hex")

        if trial_audio_hex:
            voice_id = result["voice_id"]
            audio_path = storage_path("audio", f"{voice_id}_trial.mp3")
            audio_path.write_bytes(binascii.unhexlify(trial_audio_hex))
            trial_audio_url = f"/api/voice/assets/trial/{voice_id}/download"

        self.logger.info(
            "design_voice provider=%s voice_id=%s", provider, result.get("voice_id")
        )

        return VoiceDesignResponse(
            voice_id=result["voice_id"],
            trial_audio_url=trial_audio_url,
            trial_audio_hex=trial_audio_hex,
            message=result.get("message", "设计成功"),
        )