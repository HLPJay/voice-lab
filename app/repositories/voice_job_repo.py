from sqlmodel import Session

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
