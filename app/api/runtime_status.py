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

# Max length for detail field
_MAX_DETAIL_CHARS = 120

# Action hints for each category (auth is resolved dynamically by _get_auth_hint)
_ACTION_HINTS: dict[str, str] = {
    "quota": "检查套餐额度或等待重置",
    "rate_limit": "稍后重试或降低并发",
    "timeout": "检查网络或稍后重试",
    "network": "检查网络连接",
    "server": "稍后重试",
    "validation": "检查请求参数",
    "provider": "查看调用日志",
    "unknown_error": "查看调用日志",
    "ok": "最近调用成功",
    "none": "尚无调用记录",
}


def _get_auth_hint(provider: str | None) -> str:
    """Return provider-specific API key hint for auth errors."""
    if not provider:
        return "检查当前 Provider 的 API Key 配置"
    p = provider.lower()
    if "mimo" in p or "xiaomi" in p:
        return "检查 MIMO_API_KEY"
    if "minimax" in p:
        return "检查 MINIMAX_API_KEY"
    return "检查当前 Provider 的 API Key 配置"


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


def _classify_call(entry: ProviderCallLog) -> dict[str, Any]:
    """Classify a ProviderCallLog entry into state/category/label/detail/action_hint."""
    error_type = (entry.error_type or "").lower()
    error_msg = (entry.error_message or "").lower()
    status_code = entry.status_code

    # 1. Quota issues
    if any(kw in error_msg for kw in ["usage limit", "quota", "exceeded", "plan limit", "limit reached"]):
        detail = _truncate(entry.error_message or "额度受限", _MAX_DETAIL_CHARS)
        return {
            "state": "warning",
            "category": "quota",
            "label": "额度受限",
            "detail": detail,
            "action_hint": _ACTION_HINTS["quota"],
        }

    # 2. Rate limit
    if status_code == 429 or any(kw in error_msg for kw in ["rate limit", "too many requests"]):
        detail = _truncate(entry.error_message or "请求过于频繁", _MAX_DETAIL_CHARS)
        return {
            "state": "warning",
            "category": "rate_limit",
            "label": "限流中",
            "detail": detail,
            "action_hint": _ACTION_HINTS["rate_limit"],
        }

    # 3. Auth issues
    if status_code in (401, 403) or any(kw in error_msg for kw in ["unauthorized", "forbidden", "invalid key", "api key", "auth"]):
        detail = _truncate(entry.error_message or "鉴权失败", _MAX_DETAIL_CHARS)
        return {
            "state": "error",
            "category": "auth",
            "label": "鉴权失败",
            "detail": detail,
            "action_hint": _get_auth_hint(entry.provider),
        }

    # 4. Timeout
    if any(kw in error_msg for kw in ["timeout", "timed out"]):
        detail = _truncate(entry.error_message or "请求超时", _MAX_DETAIL_CHARS)
        return {
            "state": "error",
            "category": "timeout",
            "label": "网络超时",
            "detail": detail,
            "action_hint": _ACTION_HINTS["timeout"],
        }

    # 5. Network issues
    if any(kw in error_msg for kw in ["connection", "connect", "dns", "network"]):
        detail = _truncate(entry.error_message or "网络异常", _MAX_DETAIL_CHARS)
        return {
            "state": "error",
            "category": "network",
            "label": "网络异常",
            "detail": detail,
            "action_hint": _ACTION_HINTS["network"],
        }

    # 6. Validation errors
    if status_code in (400, 422) or any(kw in error_msg for kw in ["invalid", "validation", "parameter"]):
        detail = _truncate(entry.error_message or "参数错误", _MAX_DETAIL_CHARS)
        return {
            "state": "error",
            "category": "validation",
            "label": "参数错误",
            "detail": detail,
            "action_hint": _ACTION_HINTS["validation"],
        }

    # 7. Provider-specific errors
    if "provider_error" in error_type or "provider error" in error_msg:
        detail = _truncate(entry.error_message or "Provider 调用异常", _MAX_DETAIL_CHARS)
        return {
            "state": "error",
            "category": "provider",
            "label": "Provider 异常",
            "detail": detail,
            "action_hint": _ACTION_HINTS["provider"],
        }

    # 8. Server errors (checked after more specific error types)
    if status_code is not None and status_code >= 500:
        detail = _truncate(entry.error_message or f"HTTP {status_code}", _MAX_DETAIL_CHARS)
        return {
            "state": "error",
            "category": "server",
            "label": "服务异常",
            "detail": detail,
            "action_hint": _ACTION_HINTS["server"],
        }

    # 9. Generic error with error_type set but not matching above
    if entry.error_type:
        detail = _truncate(entry.error_message or entry.error_type, _MAX_DETAIL_CHARS)
        return {
            "state": "error",
            "category": "unknown_error",
            "label": "调用异常",
            "detail": detail,
            "action_hint": _ACTION_HINTS["unknown_error"],
        }

    # 10. No error_type but non-2xx status
    if status_code is not None and status_code >= 400:
        detail = _truncate(entry.error_message or f"HTTP {status_code}", _MAX_DETAIL_CHARS)
        return {
            "state": "error",
            "category": "unknown_error",
            "label": "调用异常",
            "detail": detail,
            "action_hint": _ACTION_HINTS["unknown_error"],
        }

    # 11. Success — no error
    return {
        "state": "available",
        "category": "ok",
        "label": "正常",
        "detail": None,
        "action_hint": _ACTION_HINTS["ok"],
    }


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"


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


def _provider_status_from_entry(entry: ProviderCallLog | None) -> dict[str, Any]:
    """Build provider_status from a ProviderCallLog entry."""
    if entry is None:
        return {
            "state": "unknown",
            "category": "none",
            "label": "无调用记录",
            "detail": None,
            "action_hint": _ACTION_HINTS["none"],
            "last_seen_at": None,
            "duration_ms": None,
        }

    classification = _classify_call(entry)
    return {
        "state": classification["state"],
        "category": classification["category"],
        "label": classification["label"],
        "detail": classification["detail"],
        "action_hint": classification["action_hint"],
        "last_seen_at": entry.created_at,
        "duration_ms": entry.duration_ms,
    }


def _get_ws_model(default_provider: str, fallback: str) -> str:
    """Get the ws_model for default_provider from capability registry metadata."""
    try:
        from app.providers.capability_registry import get_capability
        cap = get_capability(default_provider)
        if cap and cap.metadata:
            ws = cap.metadata.get("ws_model")
            if ws:
                return str(ws)
        if cap and cap.tts and cap.tts.default_model:
            return cap.tts.default_model
    except Exception:
        pass
    return fallback


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
    last_call_entry = session.exec(
        select(ProviderCallLog)
        .order_by(ProviderCallLog.created_at.desc())
        .limit(1)
    ).first()
    last_call = _last_call(session)
    provider_status = _provider_status_from_entry(last_call_entry)

    default_ws_model = _get_ws_model(settings.voice_provider, settings.minimax_default_model)

    return {
        "current": {
            "default_provider": settings.voice_provider,
            "default_model": settings.minimax_default_model,
            "default_ws_model": default_ws_model,
            "default_audio_format": settings.default_audio_format,
        },
        "today": today,
        "month": month,
        "last_call": last_call,
        "provider_status": provider_status,
    }
