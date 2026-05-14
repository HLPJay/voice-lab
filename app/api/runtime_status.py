"""Runtime status API — read-only usage stats and provider state."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.database import get_session
from app.models.provider_call_log import ProviderCallLog
from app.models.voice_asset import AudioAsset
from app.models.voice_job import VoiceJob

router = APIRouter()


def _today_range() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start.isoformat(), end.isoformat()


def _month_range() -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        end = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    end = end - timedelta(seconds=1)
    return start.isoformat(), end.isoformat()


def _period_stats(session: Session, start: str, end: str) -> dict[str, int]:
    jobs = list(session.exec(
        select(VoiceJob).where(
            VoiceJob.created_at >= start,
            VoiceJob.created_at <= end,
        )
    ).all())

    call_logs = list(session.exec(
        select(ProviderCallLog).where(
            ProviderCallLog.created_at >= start,
            ProviderCallLog.created_at <= end,
        )
    ).all())

    audio_assets = list(session.exec(
        select(AudioAsset).where(
            AudioAsset.created_at >= start,
            AudioAsset.created_at <= end,
        )
    ).all())

    job_count = len(jobs)
    success_count = sum(1 for j in jobs if j.status == "success")
    failed_count = sum(1 for j in jobs if j.status == "failed")

    chars_from_logs = sum(int(l.usage_characters) for l in call_logs if l.usage_characters)
    chars_from_assets = sum(int(a.usage_characters) for a in audio_assets if a.usage_characters)
    usage_characters = max(chars_from_logs, chars_from_assets)

    return {
        "job_count": job_count,
        "success_count": success_count,
        "failed_count": failed_count,
        "usage_characters": usage_characters,
    }


def _last_call(session: Session) -> dict[str, Any]:
    entry = session.exec(
        select(ProviderCallLog)
        .order_by(ProviderCallLog.created_at.desc())
        .limit(1)
    ).first()

    if entry is None:
        return {
            "provider": None,
            "api_path": None,
            "status": "none",
            "duration_ms": None,
            "error_type": None,
            "error_message": None,
            "created_at": None,
        }

    status = "error" if entry.error_type else "success"
    return {
        "provider": entry.provider,
        "api_path": entry.api_path,
        "status": status,
        "duration_ms": entry.duration_ms,
        "error_type": entry.error_type,
        "error_message": entry.error_message,
        "created_at": entry.created_at,
    }


@router.get("/runtime/status")
def get_runtime_status(
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Return read-only runtime status: current config, today/month usage, last call state."""
    settings = get_settings()
    today_start, today_end = _today_range()
    month_start, month_end = _month_range()

    today = _period_stats(session, today_start, today_end)
    month = _period_stats(session, month_start, month_end)
    last_call = _last_call(session)

    if last_call["status"] == "none":
        provider_state = "unknown"
        provider_label = "无调用记录"
    elif last_call["status"] == "error":
        provider_state = "error"
        provider_label = "最近调用异常"
    else:
        provider_state = "available"
        provider_label = "正常"

    return {
        "current": {
            "default_provider": settings.voice_provider,
            "default_model": settings.minimax_default_model,
            "default_ws_model": settings.minimax_ws_model,
            "default_audio_format": settings.default_audio_format,
        },
        "today": today,
        "month": month,
        "last_call": last_call,
        "provider_status": {
            "state": provider_state,
            "label": provider_label,
        },
    }
