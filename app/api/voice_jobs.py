from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.errors import JobNotFound
from app.models.voice_job import VoiceJob

router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    session: Session = Depends(get_session),
):
    job = session.get(VoiceJob, job_id)
    if not job:
        raise JobNotFound("Voice job not found", job_id=job_id)
    return {
        "job_id": job.id,
        "job_type": job.job_type,
        "status": job.status,
        "provider": job.provider,
        "model": job.model,
        "profile_id": job.profile_id,
        "input_text": job.input_text,
        "processed_text": job.processed_text,
        "provider_trace_id": job.provider_trace_id,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
