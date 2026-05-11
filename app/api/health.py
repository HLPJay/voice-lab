import shutil
import time
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlmodel import Session

from app.core.config import get_settings
from app.core.database import get_session
from app.models.provider_call_log import ProviderCallLog

router = APIRouter()

_start_time = time.monotonic()


def _uptime() -> float:
    return round(time.monotonic() - _start_time)


@router.get("/health")
async def health():
    """Quick liveness probe — no dependencies checked."""
    return {"status": "ok", "app": "Voice Lab"}


@router.get("/health/detail")
async def health_detail(session: Session = Depends(get_session)) -> dict:
    """Detailed health check covering database, storage, and provider."""
    settings = get_settings()
    checks: dict = {}

    # ── Database ─────────────────────────────────────────────────
    db_latency_ms: float | None = None
    db_status = "healthy"
    try:
        t0 = time.monotonic()
        session.exec(text("SELECT 1")).one()
        db_latency_ms = round((time.monotonic() - t0) * 1000, 1)
    except Exception:
        db_status = "unhealthy"
    checks["database"] = {"status": db_status, "latency_ms": db_latency_ms}

    # ── Storage ─────────────────────────────────────────────────
    storage_path = Path(settings.storage_dir)
    storage_status = "healthy"
    writable = False
    free_space_mb: int | None = None
    try:
        if storage_path.exists():
            test_file = storage_path / ".health_check_tmp"
            test_file.write_text("")
            test_file.unlink()
            writable = True
        else:
            writable = False
    except Exception:
        storage_status = "unhealthy"

    try:
        usage = shutil.disk_usage(storage_path if storage_path.exists() else ".")
        free_space_mb = round(usage.free / (1024 * 1024), 1)
    except Exception:
        pass

    checks["storage"] = {
        "status": storage_status,
        "path": str(storage_path),
        "writable": writable,
        "free_space_mb": free_space_mb,
    }

    # ── Provider (MiniMax) ───────────────────────────────────────
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    provider_status = "unknown"
    last_call_at: str | None = None
    last_status_code: int | None = None
    total_calls_24h = 0
    error_count_24h = 0
    error_rate_24h = 0.0

    try:
        # Last call (all time)
        last_row = session.exec(
            select(ProviderCallLog.created_at, ProviderCallLog.status_code)
            .where(ProviderCallLog.provider == "minimax")
            .order_by(ProviderCallLog.created_at.desc())
            .limit(1)
        ).first()

        if last_row:
            last_call_at = last_row[0]
            last_status_code = last_row[1]

        # 24-hour window
        cutoff_24h = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 86400))

        total_calls_24h = session.exec(
            select(func.count(ProviderCallLog.id))
            .where(ProviderCallLog.provider == "minimax")
            .where(ProviderCallLog.created_at >= cutoff_24h)
        ).scalar_one() or 0

        error_count_24h = session.exec(
            select(func.count(ProviderCallLog.id))
            .where(ProviderCallLog.provider == "minimax")
            .where(ProviderCallLog.created_at >= cutoff_24h)
            .where(ProviderCallLog.error_type.isnot(None))
        ).scalar_one() or 0

        if total_calls_24h > 0:
            error_rate_24h = round(error_count_24h / total_calls_24h, 3)
            if error_rate_24h > 0.5:
                provider_status = "degraded"
            else:
                provider_status = "healthy"
    except Exception:
        pass

    checks["provider_minimax"] = {
        "status": provider_status,
        "last_call_at": last_call_at,
        "last_status_code": last_status_code,
        "total_calls_24h": total_calls_24h,
        "error_rate_24h": error_rate_24h,
    }

    # ── Overall status ───────────────────────────────────────────
    overall = "healthy"
    for check in checks.values():
        s = check.get("status", "unknown")
        if s == "unhealthy":
            overall = "unhealthy"
            break
        if s == "degraded":
            overall = "degraded"

    return {
        "status": overall,
        "version": "0.1.0",
        "uptime_seconds": _uptime(),
        "timestamp": now_iso,
        "checks": checks,
    }
