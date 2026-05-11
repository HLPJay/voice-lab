from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import VoiceBindingCreate, VoiceBindingRead, VoiceBindingUpdate
from app.services.voice_binding_service import VoiceBindingService

router = APIRouter()
service = VoiceBindingService()


@router.get("/profiles/{profile_id}/bindings", response_model=list[VoiceBindingRead])
async def list_bindings(
    profile_id: str,
    session: Session = Depends(get_session),
):
    return service.list_profile_bindings(session, profile_id)


@router.post(
    "/profiles/{profile_id}/bindings",
    response_model=VoiceBindingRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_binding(
    profile_id: str,
    request: VoiceBindingCreate,
    session: Session = Depends(get_session),
):
    return service.create_profile_binding(session, profile_id, request)


@router.patch("/bindings/{binding_id}", response_model=VoiceBindingRead)
async def update_binding(
    binding_id: str,
    request: VoiceBindingUpdate,
    session: Session = Depends(get_session),
):
    return service.update_binding(session, binding_id, request)


@router.delete("/bindings/{binding_id}", response_model=VoiceBindingRead)
async def delete_binding(
    binding_id: str,
    session: Session = Depends(get_session),
):
    return service.deprecate_binding(session, binding_id)
