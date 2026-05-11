from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.provider_call_log import ProviderCallLog
from app.services.stats_service import StatsService

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
    # Build filter conditions once (used for both count and data query)
    conditions = []
    if provider is not None:
        conditions.append(ProviderCallLog.provider == provider)
    if api_path is not None:
        conditions.append(ProviderCallLog.api_path == api_path)
    if job_id is not None:
        conditions.append(ProviderCallLog.job_id == job_id)
    if start is not None:
        conditions.append(ProviderCallLog.created_at >= start)
    if end is not None:
        conditions.append(ProviderCallLog.created_at < end)
    if status == "success":
        conditions.append(ProviderCallLog.status_code.isnot(None))
        conditions.append(ProviderCallLog.error_type.is_(None))
    elif status == "error":
        conditions.append(ProviderCallLog.error_type.isnot(None))

    # Count with same filters (no materialization)
    count_q = select(func.count(ProviderCallLog.id)).where(*conditions) if conditions else select(func.count(ProviderCallLog.id))
    total = session.exec(count_q).one() or 0

    # Data query with pagination
    limit = min(limit, 200)
    query = select(ProviderCallLog).where(*conditions) if conditions else select(ProviderCallLog)
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


@router.get("/stats/summary")
def get_stats_summary(
    start: str | None = Query(None, description="开始日期 YYYY-MM-DD"),
    end: str | None = Query(None, description="结束日期 YYYY-MM-DD"),
    session: Session = Depends(get_session),
):
    service = StatsService()
    return service.get_summary(session, start, end)


@router.get("/stats/daily")
def get_stats_daily(
    metric: str = Query("jobs", description="指标名：jobs/characters/errors/api_calls/avg_duration"),
    start: str | None = Query(None),
    end: str | None = Query(None),
    session: Session = Depends(get_session),
):
    service = StatsService()
    data = service.get_daily_trend(session, start, end, metric)
    return {"metric": metric, "data": data}
