from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.core.errors import JobNotFound
from app.domain.schemas import VoiceJobRead
from app.repositories import voice_job_repo

router = APIRouter()


@router.get("/jobs")
async def list_jobs(
    job_type: str | None = None,
    status: str | None = None,
    profile_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    jobs, total = voice_job_repo.list_jobs(
        session,
        job_type=job_type,
        status=status,
        profile_id=profile_id,
        limit=min(limit, 100),
        offset=offset,
    )
    return {
        "jobs": [
            VoiceJobRead(
                job_id=job.id,
                job_type=job.job_type,
                status=job.status,
                provider=job.provider,
                model=job.model,
                profile_id=job.profile_id,
                input_text=job.input_text,
                processed_text=job.processed_text,
                provider_trace_id=job.provider_trace_id,
                error_message=job.error_message,
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
            for job in jobs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/jobs/{job_id}", response_model=VoiceJobRead)
async def get_job(
    job_id: str,
    session: Session = Depends(get_session),
):
    job = voice_job_repo.get_job(session, job_id)
    if not job:
        raise JobNotFound("Voice job not found", job_id=job_id)
    return VoiceJobRead(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        provider=job.provider,
        model=job.model,
        profile_id=job.profile_id,
        input_text=job.input_text,
        processed_text=job.processed_text,
        provider_trace_id=job.provider_trace_id,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
