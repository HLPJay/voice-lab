import json

from sqlmodel import Session, select

from app.core.time import utc_now_iso
from app.domain.enums import BindingStatus
from app.models.voice_binding import VoiceBinding
from app.utils.id_generator import new_id


def list_bindings(
    session: Session,
    *,
    profile_id: str,
    include_deprecated: bool = False,
) -> list[VoiceBinding]:
    stmt = select(VoiceBinding).where(VoiceBinding.profile_id == profile_id)
    if not include_deprecated:
        stmt = stmt.where(VoiceBinding.status != BindingStatus.deprecated)
    stmt = stmt.order_by(VoiceBinding.priority, VoiceBinding.created_at)
    return list(session.exec(stmt).all())


def get_binding_by_id(session: Session, binding_id: str) -> VoiceBinding | None:
    return session.get(VoiceBinding, binding_id)


def find_duplicate_binding(
    session: Session,
    *,
    profile_id: str,
    provider: str,
    model: str,
    provider_voice_id: str,
    exclude_id: str | None = None,
) -> VoiceBinding | None:
    """Check if an active binding with the same profile+provider+model+voice_id already exists."""
    stmt = (
        select(VoiceBinding)
        .where(VoiceBinding.profile_id == profile_id)
        .where(VoiceBinding.provider == provider)
        .where(VoiceBinding.model == model)
        .where(VoiceBinding.provider_voice_id == provider_voice_id)
        .where(VoiceBinding.status != BindingStatus.deprecated)
    )
    if exclude_id:
        stmt = stmt.where(VoiceBinding.id != exclude_id)
    return session.exec(stmt).first()


def create_binding(
    session: Session,
    *,
    profile_id: str,
    provider: str,
    model: str,
    provider_voice_id: str,
    params: dict | None = None,
    priority: int = 1,
) -> VoiceBinding:
    now = utc_now_iso()
    binding = VoiceBinding(
        id=new_id("binding"),
        profile_id=profile_id,
        provider=provider,
        model=model,
        provider_voice_id=provider_voice_id,
        params_json=json.dumps(params or {}, ensure_ascii=False),
        priority=priority,
        status=BindingStatus.available,
        created_at=now,
        updated_at=now,
    )
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def update_binding(
    session: Session,
    binding: VoiceBinding,
    *,
    provider_voice_id: str | None = None,
    params: dict | None = None,
    priority: int | None = None,
    status: str | None = None,
) -> VoiceBinding:
    now = utc_now_iso()
    if provider_voice_id is not None:
        binding.provider_voice_id = provider_voice_id
    if params is not None:
        binding.params_json = json.dumps(params, ensure_ascii=False)
    if priority is not None:
        binding.priority = priority
    if status is not None:
        binding.status = status
    binding.updated_at = now
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def deprecate_binding(session: Session, binding: VoiceBinding) -> VoiceBinding:
    return update_binding(session, binding, status=BindingStatus.deprecated)


def deprecate_bindings_by_provider_voice(
    session: Session,
    *,
    provider: str,
    provider_voice_id: str,
) -> int:
    """Mark all active bindings matching provider+provider_voice_id as deprecated. Returns count."""
    stmt = (
        select(VoiceBinding)
        .where(VoiceBinding.provider == provider)
        .where(VoiceBinding.provider_voice_id == provider_voice_id)
        .where(VoiceBinding.status != BindingStatus.deprecated)
    )
    bindings = list(session.exec(stmt).all())
    if not bindings:
        return 0
    now = utc_now_iso()
    for b in bindings:
        b.status = BindingStatus.deprecated
        b.updated_at = now
        session.add(b)
    session.commit()
    return len(bindings)
