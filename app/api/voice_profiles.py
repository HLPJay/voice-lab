from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import VoiceProfileCreate, VoiceProfileRead
from app.services.voice_profile_service import VoiceProfileService

router = APIRouter()
service = VoiceProfileService()


@router.get("/profiles", response_model=list[VoiceProfileRead])
async def list_profiles(session: Session = Depends(get_session)):
    return service.list(session)


@router.post("/profiles", response_model=VoiceProfileRead)
async def create_profile(
    request: VoiceProfileCreate,
    session: Session = Depends(get_session),
):
    return service.create(session, request)
