from app.core.errors import VoiceLabError
from app.domain.schemas import VoiceDeleteRequest, VoiceDeleteResponse
from app.providers.registry import get_provider


class VoiceDeleteService:
    async def delete_voice(
        self,
        provider: str,
        request: VoiceDeleteRequest,
    ) -> VoiceDeleteResponse:
        if request.voice_type not in ("voice_cloning", "voice_generation"):
            raise VoiceLabError(
                "禁止删除系统音色",
                "voice_type must be voice_cloning or voice_generation",
            )
        adapter = get_provider(provider)
        result = await adapter.delete_voice(
            request.provider_voice_id, request.voice_type
        )
        return VoiceDeleteResponse(
            voice_id=result["voice_id"],
            deleted=result.get("deleted", True),
        )