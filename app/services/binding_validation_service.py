from sqlmodel import Session

from app.core.errors import ValidationError
from app.domain.enums import ProviderVoiceStatus
from app.models.voice_binding import VoiceBinding
from app.repositories.provider_voice_repo import get_provider_voice


def validate_binding_provider_voice(session: Session, binding: VoiceBinding) -> None:
    """Validate that the provider_voice referenced by a binding exists and is available.

    Raises ValidationError if:
    - provider_voice does not exist
    - provider_voice.status != available (e.g. deprecated)

    This must be called before any call to provider.render_sync() or
    provider.create_async_task() to prevent using a binding whose target
    voice has been deleted/deprecated locally while the binding record itself
    is still marked available.
    """
    pv = get_provider_voice(
        session,
        provider=binding.provider,
        provider_voice_id=binding.provider_voice_id,
    )
    if not pv:
        raise ValidationError(
            "绑定音色不存在，请重新绑定",
            f"provider={binding.provider}, provider_voice_id={binding.provider_voice_id}",
        )
    if pv.status != ProviderVoiceStatus.available:
        raise ValidationError(
            "绑定音色已下架，请重新绑定",
            f"provider={binding.provider}, provider_voice_id={binding.provider_voice_id}, status={pv.status}",
        )
