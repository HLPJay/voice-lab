from sqlmodel import Session

from app.core.time import utc_now_iso
from app.domain.schemas import VoiceRenderRequest, VoiceVariantGroupResponse, VoiceVariantRenderRequest, VoiceVariantResponse
from app.models.voice_variant import VoiceVariant, VoiceVariantGroup
from app.services.voice_render_service import VoiceRenderService
from app.utils.id_generator import new_id


class VoiceVariantService:
    def __init__(self):
        self.render_service = VoiceRenderService()

    async def render_variants(self, session: Session, request: VoiceVariantRenderRequest) -> VoiceVariantGroupResponse:
        combos = [
            {"speed": 0.85, "emotion": "sad"},
            {"speed": 0.92, "emotion": "calm"},
            {"speed": 1.0, "emotion": "neutral"},
            {"speed": 0.88, "emotion": "sad"},
            {"speed": 0.96, "emotion": "calm"},
        ][: request.variant_count]
        now = utc_now_iso()
        group = VoiceVariantGroup(id=new_id("variant_group"), scene=request.scene, input_text=request.text, created_at=now, updated_at=now)
        session.add(group)
        session.commit()
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
            session.add(variant)
            session.commit()
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
