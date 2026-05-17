import json

from sqlmodel import Session

from app.core.errors import BindingNotFound, ProfileNotFound, ValidationError
from app.domain.enums import ProviderVoiceStatus
from app.domain.schemas import VoiceBindingCreate, VoiceBindingRead, VoiceBindingUpdate
from app.models.voice_binding import VoiceBinding
from app.repositories.provider_voice_repo import get_provider_voice
from app.repositories.voice_binding_repo import (
    create_binding,
    deprecate_binding,
    find_duplicate_binding,
    get_binding_by_id,
    list_bindings,
    update_binding,
)
from app.repositories.voice_profile_repo import get_profile
from app.services.capability_validator import capability_validator


def _binding_to_read(binding: VoiceBinding, provider_voice_name: str | None = None) -> VoiceBindingRead:
    return VoiceBindingRead(
        id=binding.id,
        profile_id=binding.profile_id,
        provider=binding.provider,
        model=binding.model,
        provider_voice_id=binding.provider_voice_id,
        provider_voice_name=provider_voice_name,
        params=json.loads(binding.params_json or "{}"),
        priority=binding.priority,
        status=binding.status,
        created_at=binding.created_at,
        updated_at=binding.updated_at,
    )


class VoiceBindingService:
    def list_profile_bindings(
        self,
        session: Session,
        profile_id: str,
    ) -> list[VoiceBindingRead]:
        profile = get_profile(session, profile_id)
        if not profile:
            raise ProfileNotFound("Voice profile not found", profile_id)
        bindings = list_bindings(session, profile_id=profile_id, include_deprecated=False)
        reads = []
        for b in bindings:
            pv = get_provider_voice(session, provider=b.provider, provider_voice_id=b.provider_voice_id)
            reads.append(_binding_to_read(b, pv.name if pv else None))
        return reads

    def create_profile_binding(
        self,
        session: Session,
        profile_id: str,
        request: VoiceBindingCreate,
    ) -> VoiceBindingRead:
        profile = get_profile(session, profile_id)
        if not profile:
            raise ProfileNotFound("Voice profile not found", profile_id)
        if not profile.is_active:
            raise ValidationError(
                "该人设已归档，不能创建新绑定",
                f"PROFILE_ARCHIVED:{profile_id}",
            )

        capability_validator.validate_tts(provider=request.provider, model=request.model)

        pv = get_provider_voice(session, provider=request.provider, provider_voice_id=request.provider_voice_id)
        if not pv or pv.status != ProviderVoiceStatus.available:
            raise ValidationError(
                "Provider voice not found or not available",
                f"provider={request.provider}, provider_voice_id={request.provider_voice_id}",
            )

        duplicate = find_duplicate_binding(
            session,
            profile_id=profile_id,
            provider=request.provider,
            model=request.model,
            provider_voice_id=request.provider_voice_id,
        )
        if duplicate:
            raise ValidationError(
                "Duplicate binding",
                f"binding {duplicate.id} already links profile={profile_id} to {request.provider}/{request.model}/{request.provider_voice_id}",
            )

        binding = create_binding(
            session,
            profile_id=profile_id,
            provider=request.provider,
            model=request.model,
            provider_voice_id=request.provider_voice_id,
            params=request.params,
            priority=request.priority,
        )
        return _binding_to_read(binding, pv.name)

    def update_binding(
        self,
        session: Session,
        binding_id: str,
        request: VoiceBindingUpdate,
    ) -> VoiceBindingRead:
        binding = get_binding_by_id(session, binding_id)
        if not binding:
            raise BindingNotFound("Voice binding not found", binding_id)

        if request.provider_voice_id is not None:
            pv = get_provider_voice(session, provider=binding.provider, provider_voice_id=request.provider_voice_id)
            if not pv or pv.status != ProviderVoiceStatus.available:
                raise ValidationError(
                    "Provider voice not found or not available",
                    f"provider={binding.provider}, provider_voice_id={request.provider_voice_id}",
                )
            duplicate = find_duplicate_binding(
                session,
                profile_id=binding.profile_id,
                provider=binding.provider,
                model=binding.model,
                provider_voice_id=request.provider_voice_id,
                exclude_id=binding.id,
            )
            if duplicate:
                raise ValidationError(
                    "Duplicate binding",
                    f"binding {duplicate.id} already links profile={binding.profile_id} to {binding.provider}/{binding.model}/{request.provider_voice_id}",
                )

        updated = update_binding(
            session,
            binding,
            provider_voice_id=request.provider_voice_id,
            params=request.params,
            priority=request.priority,
            status=request.status,
        )

        pv = get_provider_voice(session, provider=updated.provider, provider_voice_id=updated.provider_voice_id)
        return _binding_to_read(updated, pv.name if pv else None)

    def deprecate_binding(self, session: Session, binding_id: str) -> VoiceBindingRead:
        binding = get_binding_by_id(session, binding_id)
        if not binding:
            raise BindingNotFound("Voice binding not found", binding_id)
        updated = deprecate_binding(session, binding)
        pv = get_provider_voice(session, provider=updated.provider, provider_voice_id=updated.provider_voice_id)
        return _binding_to_read(updated, pv.name if pv else None)
