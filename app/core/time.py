from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def date_path() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
