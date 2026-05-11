from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.provider_call_log import ProviderCallLog

router = APIRouter()


class CallLogItem(BaseModel):
    id: str
    request_id: str | None
    job_id: str | None
    provider: str
    api_path: str
    method: str
    status_code: int | None
    duration_ms: int | None
    provider_trace_id: str | None
    usage_characters: int | None
    error_type: str | None
    error_message: str | None
    created_at: str


class CallLogListResponse(BaseModel):
    logs: list[CallLogItem]
    total: int
    limit: int
    offset: int


@router.get("/call-logs", response_model=CallLogListResponse)
def list_call_logs(
    provider: str | None = None,
    api_path: str | None = None,
    job_id: str | None = None,
    start: str | None = None,
    end: str | None = None,
    status: Literal["success", "error"] | None = None,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
) -> CallLogListResponse:
    query = select(ProviderCallLog)

    if provider is not None:
        query = query.where(ProviderCallLog.provider == provider)
    if api_path is not None:
        query = query.where(ProviderCallLog.api_path == api_path)
    if job_id is not None:
        query = query.where(ProviderCallLog.job_id == job_id)
    if start is not None:
        query = query.where(ProviderCallLog.created_at >= start)
    if end is not None:
        query = query.where(ProviderCallLog.created_at < end)
    if status == "success":
        query = query.where(ProviderCallLog.status_code.isnot(None))
        query = query.where(ProviderCallLog.error_type.is_(None))
    elif status == "error":
        query = query.where(ProviderCallLog.error_type.isnot(None))

    # Total count (before pagination)
    count_query = select(ProviderCallLog.id)
    if provider is not None:
        count_query = count_query.where(ProviderCallLog.provider == provider)
    if api_path is not None:
        count_query = count_query.where(ProviderCallLog.api_path == api_path)
    if job_id is not None:
        count_query = count_query.where(ProviderCallLog.job_id == job_id)
    if start is not None:
        count_query = count_query.where(ProviderCallLog.created_at >= start)
    if end is not None:
        count_query = count_query.where(ProviderCallLog.created_at < end)
    if status == "success":
        count_query = count_query.where(ProviderCallLog.status_code.isnot(None))
        count_query = count_query.where(ProviderCallLog.error_type.is_(None))
    elif status == "error":
        count_query = count_query.where(ProviderCallLog.error_type.isnot(None))
    total = len(session.exec(count_query).all())

    # Apply pagination and ordering
    limit = min(limit, 200)
    query = query.order_by(ProviderCallLog.created_at.desc()).offset(offset).limit(limit)

    rows = session.exec(query).all()

    logs = [
        CallLogItem(
            id=row.id,
            request_id=row.request_id,
            job_id=row.job_id,
            provider=row.provider,
            api_path=row.api_path,
            method=row.method,
            status_code=row.status_code,
            duration_ms=row.duration_ms,
            provider_trace_id=row.provider_trace_id,
            usage_characters=row.usage_characters,
            error_type=row.error_type,
            error_message=row.error_message,
            created_at=row.created_at,
        )
        for row in rows
    ]

    return CallLogListResponse(logs=logs, total=total, limit=limit, offset=offset)
