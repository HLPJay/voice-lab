from datetime import datetime, timedelta


def _fill_zero_dates(data: list[dict], start: str | None, end: str | None) -> list[dict]:
    """Fill in missing dates in range [start, end) with value=0."""
    if not data:
        return data
    # Build a dict for quick lookup
    by_date = {d["date"]: d["value"] for d in data}
    # Determine date range
    if start and end:
        try:
            cur = datetime.strptime(start[:10], "%Y-%m-%d")
            end_dt = datetime.strptime(end[:10], "%Y-%m-%d")
            result = []
            while cur < end_dt:
                date_str = cur.strftime("%Y-%m-%d")
                result.append({"date": date_str, "value": by_date.get(date_str, 0)})
                cur += timedelta(days=1)
            return result
        except (ValueError, IndexError):
            return data
    return data

from sqlalchemy import case, func
from sqlmodel import Session, select

from app.models.provider_call_log import ProviderCallLog
from app.models.voice_asset import AudioAsset
from app.models.voice_job import VoiceJob


def _error_count():
    """Return a SQL expression that counts rows where error_type is not null,
    OR status_code >= 400, OR status_code is null (no successful HTTP response recorded)."""
    return func.sum(case(
        (
            ProviderCallLog.error_type.isnot(None)
            | (ProviderCallLog.status_code >= 400)
            | (ProviderCallLog.status_code.is_(None)),
            1
        ),
        else_=0
    ))


class StatsService:
    def get_summary(
        self, session: Session, start: str | None = None, end: str | None = None
    ) -> dict:
        """聚合总览 + 按 provider/API/天 的统计。"""
        job_filter = []
        call_filter = []
        if start:
            job_filter.append(VoiceJob.created_at >= start)
            call_filter.append(ProviderCallLog.created_at >= start)
        if end:
            job_filter.append(VoiceJob.created_at < end)
            call_filter.append(ProviderCallLog.created_at < end)

        # overview: from voice_jobs
        job_query = select(VoiceJob)
        if job_filter:
            job_query = job_query.where(*job_filter)
        all_jobs = list(session.exec(job_query).all())
        total_jobs = len(all_jobs)
        success_jobs = sum(1 for j in all_jobs if j.status == "success")
        failed_jobs = sum(1 for j in all_jobs if j.status == "failed")
        success_rate = round(success_jobs / total_jobs, 3) if total_jobs > 0 else 0

        # total_characters: use ProviderCallLog.usage_characters where set,
        # fall back to AudioAsset.usage_characters (populated for both sync and async jobs).
        # MAX handles the case where both are set (sync jobs): they should be equal,
        # so we don't double-count. For async jobs, only AudioAsset has the value.
        chars_from_calls = select(
            func.coalesce(func.sum(ProviderCallLog.usage_characters), 0)
        )
        if call_filter:
            chars_from_calls = chars_from_calls.where(*call_filter)
        chars_from_calls_val = session.exec(chars_from_calls).one() or 0

        chars_from_assets = select(
            func.coalesce(func.sum(AudioAsset.usage_characters), 0)
        )
        if job_filter:
            chars_from_assets = chars_from_assets.where(
                AudioAsset.job_id.in_(select(VoiceJob.id).where(*job_filter))
            )
        chars_from_assets_val = session.exec(chars_from_assets).one() or 0

        total_characters = max(chars_from_calls_val, chars_from_assets_val)

        # total_audio_duration_ms from AudioAsset
        dur_query = select(func.coalesce(func.sum(AudioAsset.duration_ms), 0))
        if job_filter:
            dur_query = dur_query.where(
                AudioAsset.job_id.in_(select(VoiceJob.id).where(*job_filter))
            )
        total_audio_duration_ms = session.exec(dur_query).one() or 0

        # by_provider from provider_call_logs + AudioAsset fallback for chars
        by_provider: dict = {}
        provider_query = select(
            ProviderCallLog.provider,
            func.count(ProviderCallLog.id).label("api_calls"),
            func.coalesce(func.avg(ProviderCallLog.duration_ms), 0).label("avg_ms"),
            _error_count().label("error_count"),
            func.coalesce(func.sum(ProviderCallLog.usage_characters), 0).label("chars"),
        ).group_by(ProviderCallLog.provider)
        if call_filter:
            provider_query = provider_query.where(*call_filter)

        # Get chars per provider from AudioAsset as fallback
        asset_chars_by_provider: dict = {}
        asset_chars_query = select(
            AudioAsset.provider,
            func.coalesce(func.sum(AudioAsset.usage_characters), 0).label("chars"),
        )
        if job_filter:
            asset_chars_query = asset_chars_query.where(
                AudioAsset.job_id.in_(select(VoiceJob.id).where(*job_filter))
            )
        asset_chars_query = asset_chars_query.group_by(AudioAsset.provider)
        for row in session.exec(asset_chars_query).all():
            asset_chars_by_provider[row[0]] = int(row[1] or 0)

        for row in session.exec(provider_query).all():
            p = row[0]
            api_calls = int(row[1] or 0)
            avg_ms = row[2] or 0
            error_count = int(row[3] or 0)
            call_chars = int(row[4] or 0)
            asset_chars = asset_chars_by_provider.get(p, 0)
            chars = max(call_chars, asset_chars)  # use higher of the two to avoid missing async chars
            p95 = self._p95_duration(session, p, call_filter)
            by_provider[p] = {
                "api_calls": api_calls,
                "avg_duration_ms": round(float(avg_ms)),
                "p95_duration_ms": p95,
                "error_count": error_count,
                "error_rate": round(error_count / api_calls, 3) if api_calls > 0 else 0,
                "characters_used": chars,
            }

        # by_api from provider_call_logs
        by_api: dict = {}
        api_query = select(
            ProviderCallLog.api_path,
            func.count(ProviderCallLog.id).label("calls"),
            func.coalesce(func.avg(ProviderCallLog.duration_ms), 0).label("avg_ms"),
            _error_count().label("errors"),
        ).group_by(ProviderCallLog.api_path)
        if call_filter:
            api_query = api_query.where(*call_filter)
        for row in session.exec(api_query).all():
            by_api[row[0]] = {
                "calls": int(row[1] or 0),
                "avg_ms": round(float(row[2] or 0)),
                "errors": int(row[3] or 0),
            }

        # by_day from provider_call_logs + AudioAsset fallback for chars
        by_day: list[dict] = []
        day_query = (
            select(
                func.substr(ProviderCallLog.created_at, 1, 10).label("date"),
                func.count(ProviderCallLog.id).label("api_calls"),
                _error_count().label("errors"),
                func.coalesce(func.sum(ProviderCallLog.usage_characters), 0).label("chars"),
            )
            .group_by(func.substr(ProviderCallLog.created_at, 1, 10))
            .order_by(func.substr(ProviderCallLog.created_at, 1, 10))
        )
        if call_filter:
            day_query = day_query.where(*call_filter)

        # Get chars per date from AudioAsset as fallback
        asset_chars_by_date: dict = {}
        asset_day_query = select(
            func.substr(AudioAsset.created_at, 1, 10).label("date"),
            func.coalesce(func.sum(AudioAsset.usage_characters), 0).label("chars"),
        )
        if job_filter:
            asset_day_query = asset_day_query.where(
                AudioAsset.job_id.in_(select(VoiceJob.id).where(*job_filter))
            )
        asset_day_query = asset_day_query.group_by(
            func.substr(AudioAsset.created_at, 1, 10)
        ).order_by(func.substr(AudioAsset.created_at, 1, 10))
        for row in session.exec(asset_day_query).all():
            asset_chars_by_date[row[0]] = int(row[1] or 0)

        for row in session.exec(day_query).all():
            date = row[0]
            day_jobs_query = (
                select(func.count(VoiceJob.id))
                .where(func.substr(VoiceJob.created_at, 1, 10) == date)
            )
            if job_filter:
                day_jobs_query = day_jobs_query.where(*job_filter)
            day_jobs = session.exec(day_jobs_query).one() or 0
            call_chars = int(row[3] or 0)
            asset_chars = asset_chars_by_date.get(date, 0)
            chars = max(call_chars, asset_chars)
            by_day.append(
                {
                    "date": date,
                    "jobs": int(day_jobs or 0),
                    "characters": chars,
                    "errors": int(row[2] or 0),
                    "api_calls": int(row[1] or 0),
                }
            )

        return {
            "period": {"start": start, "end": end},
            "overview": {
                "total_jobs": total_jobs,
                "success_jobs": success_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": success_rate,
                "total_characters": int(total_characters),
                "total_audio_duration_ms": int(total_audio_duration_ms),
            },
            "by_provider": by_provider,
            "by_api": by_api,
            "by_day": by_day,
        }

    def _p95_duration(
        self, session: Session, provider: str, call_filter: list
    ) -> int:
        """Return approximate P95 of duration_ms for a provider using DB-level sort + LIMIT."""
        base_conditions = [
            ProviderCallLog.provider == provider,
            ProviderCallLog.duration_ms.isnot(None),
        ]
        if call_filter:
            base_conditions.extend(call_filter)
        count_q = select(func.count(ProviderCallLog.id)).where(*base_conditions)
        total = session.exec(count_q).one() or 0
        if total == 0:
            return 0
        offset = min(int(total * 0.95) - 1, total - 1)
        offset = max(offset, 0)
        query = (
            select(ProviderCallLog.duration_ms)
            .where(*base_conditions)
            .order_by(ProviderCallLog.duration_ms)
            .offset(offset)
            .limit(1)
        )
        result = session.exec(query).first()
        return int(result) if result else 0

    def get_daily_trend(
        self, session: Session, start: str | None = None, end: str | None = None, metric: str = "jobs"
    ) -> list[dict]:
        """按天返回指标趋势数据。"""
        # Separate date filters: jobs use VoiceJob.created_at, others use ProviderCallLog.created_at
        job_filters = []
        call_filters = []
        if start:
            job_filters.append(VoiceJob.created_at >= start)
            call_filters.append(ProviderCallLog.created_at >= start)
        if end:
            job_filters.append(VoiceJob.created_at < end)
            call_filters.append(ProviderCallLog.created_at < end)

        if metric == "jobs":
            query = (
                select(
                    func.substr(VoiceJob.created_at, 1, 10).label("date"),
                    func.count(VoiceJob.id).label("value"),
                )
                .group_by(func.substr(VoiceJob.created_at, 1, 10))
                .order_by(func.substr(VoiceJob.created_at, 1, 10))
            )
            if job_filters:
                query = query.where(*job_filters)
            data = [{"date": row[0], "value": int(row[1] or 0)} for row in session.exec(query).all()]
            return _fill_zero_dates(data, start, end)

        # All other metrics use ProviderCallLog
        if metric == "characters":
            # Build call_chars_by_date from ProviderCallLog
            call_chars_by_date: dict = {}
            call_q = (
                select(
                    func.substr(ProviderCallLog.created_at, 1, 10).label("date"),
                    func.coalesce(func.sum(ProviderCallLog.usage_characters), 0).label("chars"),
                )
                .group_by(func.substr(ProviderCallLog.created_at, 1, 10))
                .order_by(func.substr(ProviderCallLog.created_at, 1, 10))
            )
            if call_filters:
                call_q = call_q.where(*call_filters)
            for row in session.exec(call_q).all():
                call_chars_by_date[row[0]] = int(row[1] or 0)

            # Build asset_chars_by_date from AudioAsset
            asset_chars_by_date: dict = {}
            asset_q = (
                select(
                    func.substr(AudioAsset.created_at, 1, 10).label("date"),
                    func.coalesce(func.sum(AudioAsset.usage_characters), 0).label("chars"),
                )
                .group_by(func.substr(AudioAsset.created_at, 1, 10))
                .order_by(func.substr(AudioAsset.created_at, 1, 10))
            )
            if job_filters:
                asset_q = asset_q.where(
                    AudioAsset.job_id.in_(select(VoiceJob.id).where(*job_filters))
                )
            for row in session.exec(asset_q).all():
                asset_chars_by_date[row[0]] = int(row[1] or 0)

            # Merge: use max of call and asset chars per date
            dates = sorted(set(call_chars_by_date) | set(asset_chars_by_date))
            data = [
                {
                    "date": date,
                    "value": max(call_chars_by_date.get(date, 0), asset_chars_by_date.get(date, 0)),
                }
                for date in dates
            ]
            return _fill_zero_dates(data, start, end)

        if metric == "errors":
            q = (
                select(
                    func.substr(ProviderCallLog.created_at, 1, 10).label("date"),
                    _error_count().label("value"),
                )
                .group_by(func.substr(ProviderCallLog.created_at, 1, 10))
                .order_by(func.substr(ProviderCallLog.created_at, 1, 10))
            )
            if call_filters:
                q = q.where(*call_filters)
            return _fill_zero_dates([{"date": r[0], "value": int(r[1] or 0)} for r in session.exec(q).all()], start, end)

        if metric == "api_calls":
            q = (
                select(
                    func.substr(ProviderCallLog.created_at, 1, 10).label("date"),
                    func.count(ProviderCallLog.id).label("value"),
                )
                .group_by(func.substr(ProviderCallLog.created_at, 1, 10))
                .order_by(func.substr(ProviderCallLog.created_at, 1, 10))
            )
            if call_filters:
                q = q.where(*call_filters)
            return _fill_zero_dates([{"date": r[0], "value": int(r[1] or 0)} for r in session.exec(q).all()], start, end)

        if metric == "avg_duration":
            q = (
                select(
                    func.substr(ProviderCallLog.created_at, 1, 10).label("date"),
                    func.coalesce(func.avg(ProviderCallLog.duration_ms), 0).label("value"),
                )
                .group_by(func.substr(ProviderCallLog.created_at, 1, 10))
                .order_by(func.substr(ProviderCallLog.created_at, 1, 10))
            )
            if call_filters:
                q = q.where(*call_filters)
            return _fill_zero_dates([{"date": r[0], "value": round(float(r[1] or 0))} for r in session.exec(q).all()], start, end)

        return []
