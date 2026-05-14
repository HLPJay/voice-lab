from sqlmodel import Session, select, func

from app.core.time import utc_now_iso
from app.models.voice_job import VoiceJob


def get_job(session: Session, job_id: str) -> VoiceJob | None:
    return session.get(VoiceJob, job_id)


def create_job(session: Session, job: VoiceJob) -> VoiceJob:
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def update_job(session: Session, job: VoiceJob) -> VoiceJob:
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def soft_delete_job(session: Session, job: VoiceJob) -> VoiceJob:
    job.status = "deleted"
    job.updated_at = utc_now_iso()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def list_jobs(
    session: Session,
    *,
    job_type: str | None = None,
    status: str | None = None,
    profile_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[VoiceJob], int]:
    """Return (jobs, total_count)."""
    conditions = []

    if status is not None:
        conditions.append(VoiceJob.status == status)
    else:
        conditions.append(VoiceJob.status != "deleted")

    if job_type is not None:
        conditions.append(VoiceJob.job_type == job_type)
    if profile_id is not None:
        conditions.append(VoiceJob.profile_id == profile_id)

    count_q = select(func.count(VoiceJob.id)).where(*conditions) if conditions else select(func.count(VoiceJob.id))
    total = session.exec(count_q).one() or 0

    query = select(VoiceJob).where(*conditions) if conditions else select(VoiceJob)
    query = query.order_by(VoiceJob.created_at.desc()).offset(offset).limit(limit)
    jobs = list(session.exec(query).all())

    return jobs, total
