#!/usr/bin/env python3
"""
Analyze provider errors from ProviderCallLog.

Groups errors by error_type, error_message, status_code, api_path, and provider
to identify patterns and attribution.

Usage:
    python scripts/analyze_provider_errors.py --days 7 --top 20
    python scripts/analyze_provider_errors.py --provider minimax --days 30
    python scripts/analyze_provider_errors.py --error-type ValidationError --top 50
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from sqlmodel import Session, select, func

from app.core.database import get_engine
from app.models.provider_call_log import ProviderCallLog
from app.models.voice_job import VoiceJob


def parse_date(date_str: str) -> str:
    """Parse and validate date string as YYYY-MM-DD."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")


def analyze_errors(
    days: int | None = None,
    start: str | None = None,
    end: str | None = None,
    provider: str | None = None,
    error_type: str | None = None,
    top: int = 20,
) -> dict:
    """Analyze provider errors from the database."""
    engine = get_engine()

    # Build filters
    call_filter = []
    job_filter = []

    if start:
        call_filter.append(ProviderCallLog.created_at >= start)
        job_filter.append(VoiceJob.created_at >= start)
    elif days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        call_filter.append(ProviderCallLog.created_at >= cutoff)
        job_filter.append(VoiceJob.created_at >= cutoff)

    if end:
        call_filter.append(ProviderCallLog.created_at < end)
        job_filter.append(VoiceJob.created_at < end)

    if provider:
        call_filter.append(ProviderCallLog.provider == provider)

    if error_type:
        call_filter.append(ProviderCallLog.error_type == error_type)
    else:
        # Only errors (error_type IS NOT NULL)
        call_filter.append(ProviderCallLog.error_type.isnot(None))

    with Session(engine) as session:
        # Overall error stats
        error_query = select(
            ProviderCallLog.error_type,
            func.count(ProviderCallLog.id).label("count"),
        ).group_by(ProviderCallLog.error_type).order_by(func.count(ProviderCallLog.id).desc())

        if call_filter:
            error_query = error_query.where(*call_filter)

        error_types = []
        for row in session.exec(error_query).all():
            error_types.append({"error_type": row[0], "count": int(row[1])})

        # By error_message grouping (first 100 chars for grouping)
        msg_query = select(
            func.substr(ProviderCallLog.error_message, 1, 100).label("msg_prefix"),
            ProviderCallLog.error_type,
            ProviderCallLog.provider,
            func.count(ProviderCallLog.id).label("count"),
            func.max(ProviderCallLog.created_at).label("last_seen"),
        ).group_by(
            func.substr(ProviderCallLog.error_message, 1, 100),
            ProviderCallLog.error_type,
            ProviderCallLog.provider,
        ).order_by(func.count(ProviderCallLog.id).desc())

        if call_filter:
            msg_query = msg_query.where(*call_filter)

        msg_groups = []
        for row in session.exec(msg_query.limit(top * 2)).all():
            msg_groups.append({
                "error_message_prefix": row[0],
                "error_type": row[1],
                "provider": row[2],
                "count": int(row[3]),
                "last_seen": row[4],
            })

        # By api_path + status_code
        api_query = select(
            ProviderCallLog.api_path,
            ProviderCallLog.status_code,
            ProviderCallLog.error_type,
            func.count(ProviderCallLog.id).label("count"),
        ).group_by(
            ProviderCallLog.api_path,
            ProviderCallLog.status_code,
            ProviderCallLog.error_type,
        ).order_by(func.count(ProviderCallLog.id).desc())

        if call_filter:
            api_query = api_query.where(*call_filter)

        api_groups = []
        for row in session.exec(api_query.limit(top)).all():
            api_groups.append({
                "api_path": row[0],
                "status_code": row[1],
                "error_type": row[2],
                "count": int(row[3]),
            })

        # By provider
        provider_query = select(
            ProviderCallLog.provider,
            ProviderCallLog.error_type,
            func.count(ProviderCallLog.id).label("count"),
        ).group_by(
            ProviderCallLog.provider,
            ProviderCallLog.error_type,
        ).order_by(func.count(ProviderCallLog.id).desc())

        if call_filter:
            provider_query = provider_query.where(*call_filter)

        provider_groups = []
        for row in session.exec(provider_query).all():
            provider_groups.append({
                "provider": row[0],
                "error_type": row[1],
                "count": int(row[2]),
            })

        # Total error count
        total_query = select(func.count(ProviderCallLog.id)).where(*call_filter)
        total_errors = session.exec(total_query).one() or 0

        # Total calls in period
        total_calls_query = select(func.count(ProviderCallLog.id))
        if call_filter:
            # Remove error_type filter for total
            non_error_filter = [f for f in call_filter if not str(f).startswith("error_type")]
            if non_error_filter:
                total_calls_query = total_calls_query.where(*non_error_filter)
        total_calls = session.exec(total_calls_query).one() or 0

        return {
            "period": {
                "days": days,
                "start": start,
                "end": end,
            },
            "filters": {
                "provider": provider,
                "error_type": error_type,
            },
            "total_calls": total_calls,
            "total_errors": total_errors,
            "error_rate": round(total_errors / total_calls, 4) if total_calls > 0 else 0,
            "by_error_type": error_types,
            "by_error_message": msg_groups[:top],
            "by_api_path": api_groups[:top],
            "by_provider": provider_groups,
        }


def print_report(data: dict, top: int = 20):
    """Print a human-readable error analysis report."""
    print("=" * 80)
    print("PROVIDER ERROR ANALYSIS REPORT")
    print("=" * 80)
    print(f"Period: {data['period']}")
    print(f"Filters: provider={data['filters']['provider']}, error_type={data['filters']['error_type']}")
    print()
    print(f"Total API calls: {data['total_calls']}")
    print(f"Total errors:    {data['total_errors']}")
    print(f"Error rate:       {data['error_rate']:.2%}")
    print()

    print("-" * 80)
    print("ERRORS BY TYPE")
    print("-" * 80)
    for item in data["by_error_type"]:
        print(f"  {item['error_type']}: {item['count']}")
    print()

    print("-" * 80)
    print(f"TOP {top} ERROR MESSAGE GROUPS")
    print("-" * 80)
    print(f"{'Count':>8}  {'Provider':>12}  {'Error Type':>20}  Message Prefix")
    print("-" * 80)
    for item in data["by_error_message"]:
        msg = item["error_message_prefix"] or "(empty)"
        if len(msg) > 50:
            msg = msg[:47] + "..."
        print(f"{item['count']:>8}  {item['provider']:>12}  {item['error_type']:>20}  {msg}")
    print()

    print("-" * 80)
    print(f"ERRORS BY API PATH (top {top})")
    print("-" * 80)
    print(f"{'Count':>8}  {'API Path':>30}  {'Status':>8}  Error Type")
    print("-" * 80)
    for item in data["by_api_path"]:
        path = item["api_path"] or "(unknown)"
        if len(path) > 30:
            path = path[:27] + "..."
        print(f"{item['count']:>8}  {path:>30}  {str(item['status_code'] or 'N/A'):>8}  {item['error_type']}")
    print()

    print("-" * 80)
    print("ERRORS BY PROVIDER")
    print("-" * 80)
    print(f"{'Provider':>20}  {'Error Type':>25}  Count")
    print("-" * 80)
    for item in data["by_provider"]:
        print(f"{item['provider']:>20}  {item['error_type']:>25}  {item['count']}")
    print()

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze provider errors from ProviderCallLog"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)",
    )
    parser.add_argument(
        "--start",
        type=parse_date,
        help="Start date (YYYY-MM-DD). Overrides --days if provided.",
    )
    parser.add_argument(
        "--end",
        type=parse_date,
        help="End date (YYYY-MM-DD, exclusive).",
    )
    parser.add_argument(
        "--provider",
        type=str,
        help="Filter by provider (e.g., minimax)",
    )
    parser.add_argument(
        "--error-type",
        type=str,
        help="Filter by specific error type (e.g., ValidationError)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top results to show (default: 20)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of human-readable report",
    )

    args = parser.parse_args()

    if args.start and not args.end:
        # Default end to today
        args.end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    data = analyze_errors(
        days=args.days if not args.start else None,
        start=args.start,
        end=args.end,
        provider=args.provider,
        error_type=args.error_type,
        top=args.top,
    )

    if args.json:
        import json
        print(json.dumps(data, indent=2, default=str))
    else:
        print_report(data, top=args.top)


if __name__ == "__main__":
    main()