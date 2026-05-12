from sqlmodel import Session

from app.core.errors import VoiceLabError
from app.domain.schemas import VoiceDeleteRequest, VoiceDeleteResponse
from app.providers.registry import get_provider
from app.repositories.provider_voice_repo import mark_provider_voice_deprecated
from app.repositories.voice_binding_repo import deprecate_bindings_by_provider_voice


class VoiceDeleteService:
    async def delete_voice(
        self,
        session: Session,
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

        local_provider_voice_updated = mark_provider_voice_deprecated(
            session,
            provider=provider,
            provider_voice_id=request.provider_voice_id,
        )

        affected_bindings_count = deprecate_bindings_by_provider_voice(
            session,
            provider=provider,
            provider_voice_id=request.provider_voice_id,
        )

        return VoiceDeleteResponse(
            voice_id=result["voice_id"],
            deleted=result.get("deleted", True),
            message="删除成功",
            local_provider_voice_updated=local_provider_voice_updated,
            affected_bindings_count=affected_bindings_count,
        )
