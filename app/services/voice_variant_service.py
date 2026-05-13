from sqlmodel import Session

from app.core.time import utc_now_iso
from app.domain.schemas import VoiceRenderRequest, VoiceVariantGroupResponse, VoiceVariantRenderRequest, VoiceVariantResponse
from app.models.voice_variant import VoiceVariant, VoiceVariantGroup
from app.repositories import voice_variant_repo
from app.services.cost_guard_service import CostGuardService
from app.services.resource_guard_service import get_resource_guard
from app.services.voice_render_service import VoiceRenderService
from app.utils.id_generator import new_id


class VoiceVariantService:
    def __init__(self):
        self.render_service = VoiceRenderService()
        self.cost_guard = CostGuardService()

    async def render_variants(self, session: Session, request: VoiceVariantRenderRequest) -> VoiceVariantGroupResponse:
        provider = request.provider or "mock"
        self.cost_guard.require_confirmed(provider, "voice_variants", request.confirm_cost)
        combos = [
            {"speed": 0.85, "emotion": "sad"},
            {"speed": 0.92, "emotion": "calm"},
            {"speed": 1.0, "emotion": "neutral"},
            {"speed": 0.88, "emotion": "sad"},
            {"speed": 0.96, "emotion": "calm"},
        ][: request.variant_count]
        now = utc_now_iso()
        group = VoiceVariantGroup(id=new_id("variant_group"), scene=request.scene, input_text=request.text, created_at=now, updated_at=now)
        group = voice_variant_repo.create_group(session, group)

        async with get_resource_guard().guard(
            provider=provider,
            operation="voice_variants",
            model=None,
            job_id=None,
        ):
            responses: list[VoiceVariantResponse] = []
            for combo in combos:
                render_response = await self.render_service.render_voice(
                    session,
                    VoiceRenderRequest(
                        text=request.text,
                        profile_id=request.profile_id,
                        provider=request.provider,
                        need_subtitle=request.need_subtitle,
                    ),
                    voice_overrides=combo,
                )
                variant = VoiceVariant(
                    id=new_id("variant"),
                    group_id=group.id,
                    job_id=render_response.job_id,
                    profile_id=request.profile_id,
                    audio_asset_id=render_response.audio_asset.id if render_response.audio_asset else None,
                    speed=combo["speed"],
                    emotion=combo["emotion"],
                    created_at=utc_now_iso(),
                )
                variant = voice_variant_repo.create_variant(session, variant)
                responses.append(
                    VoiceVariantResponse(
                        variant_id=variant.id,
                        job_id=variant.job_id,
                        profile_id=request.profile_id,
                        speed=variant.speed,
                        emotion=variant.emotion,
                        audio_asset_id=variant.audio_asset_id,
                        audio_url=render_response.audio_asset.url if render_response.audio_asset else None,
                        duration_ms=render_response.audio_asset.duration_ms if render_response.audio_asset else None,
                    )
                )
        return VoiceVariantGroupResponse(group_id=group.id, variants=responses)
