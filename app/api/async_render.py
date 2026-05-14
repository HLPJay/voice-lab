from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.domain.schemas import (
    AsyncJobStatusResponse,
    AsyncRenderRequest,
    AsyncRenderResponse,
)
from app.services.async_render_service import AsyncRenderService
from app.services.capability_validator import capability_validator

router = APIRouter()
service = AsyncRenderService()


@router.post("/render/async", response_model=AsyncRenderResponse)
async def submit_async_render(
    request: AsyncRenderRequest,
    session: Session = Depends(get_session),
):
    capability_validator.validate_tts(
        provider=request.provider,
        text=request.text,
        audio_format=request.audio_format,
        need_subtitle=request.need_subtitle,
    )
    return await service.submit_task(session, request)


@router.get("/render/async/{job_id}/status", response_model=AsyncJobStatusResponse)
async def query_async_status(
    job_id: str,
    session: Session = Depends(get_session),
):
    return await service.query_status(session, job_id)
