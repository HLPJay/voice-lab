from sqlalchemy import case, func

from sqlmodel import Session, select

from app.models.provider_call_log import ProviderCallLog
from app.models.voice_asset import AudioAsset
from app.models.voice_job import VoiceJob


def _error_count():
    """Return a SQL expression that counts rows where error_type is not null."""
    return func.sum(case((ProviderCallLog.error_type.isnot(None), 1), else_=0))


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

        # total_characters from provider_call_logs
        char_query = select(func.coalesce(func.sum(ProviderCallLog.usage_characters), 0))
        if call_filter:
            char_query = char_query.where(*call_filter)
        total_characters = session.exec(char_query).one() or 0

        # total_audio_duration_ms from AudioAsset
        dur_query = select(func.coalesce(func.sum(AudioAsset.duration_ms), 0))
        if job_filter:
            dur_query = dur_query.where(
                AudioAsset.job_id.in_(select(VoiceJob.id).where(*job_filter))
            )
        total_audio_duration_ms = session.exec(dur_query).one() or 0

        # by_provider from provider_call_logs
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
        for row in session.exec(provider_query).all():
            p = row[0]
            api_calls = int(row[1] or 0)
            avg_ms = row[2] or 0
            error_count = int(row[3] or 0)
            chars = int(row[4] or 0)
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

        # by_day from provider_call_logs
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
        for row in session.exec(day_query).all():
            date = row[0]
            day_jobs_query = (
                select(func.count(VoiceJob.id))
                .where(func.substr(VoiceJob.created_at, 1, 10) == date)
            )
            if job_filter:
                day_jobs_query = day_jobs_query.where(*job_filter)
            day_jobs = session.exec(day_jobs_query).one() or 0
            by_day.append(
                {
                    "date": date,
                    "jobs": int(day_jobs or 0),
                    "characters": int(row[3] or 0),
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
        """Return approximate P95 of duration_ms for a provider."""
        query = (
            select(ProviderCallLog.duration_ms)
            .where(ProviderCallLog.provider == provider)
            .where(ProviderCallLog.duration_ms.isnot(None))
            .order_by(ProviderCallLog.duration_ms)
        )
        if call_filter:
            query = query.where(*call_filter)
        durations = [r for r in session.exec(query).all() if r is not None]
        if not durations:
            return 0
        idx = int(len(durations) * 0.95)
        if idx >= len(durations):
            idx = len(durations) - 1
        return durations[idx]

    def get_daily_trend(
        self, session: Session, start: str | None = None, end: str | None = None, metric: str = "jobs"
    ) -> list[dict]:
        """按天返回指标趋势数据。"""
        filters = []
        if start:
            filters.append(ProviderCallLog.created_at >= start)
        if end:
            filters.append(ProviderCallLog.created_at < end)

        if metric == "jobs":
            query = (
                select(
                    func.substr(VoiceJob.created_at, 1, 10).label("date"),
                    func.count(VoiceJob.id).label("value"),
                )
                .group_by(func.substr(VoiceJob.created_at, 1, 10))
                .order_by(func.substr(VoiceJob.created_at, 1, 10))
            )
            if filters:
                query = query.where(*filters)
            return [
                {"date": row[0], "value": int(row[1] or 0)}
                for row in session.exec(query).all()
            ]

        if metric == "characters":
            query = (
                select(
                    func.substr(ProviderCallLog.created_at, 1, 10).label("date"),
                    func.coalesce(func.sum(ProviderCallLog.usage_characters), 0).label("value"),
                )
                .group_by(func.substr(ProviderCallLog.created_at, 1, 10))
                .order_by(func.substr(ProviderCallLog.created_at, 1, 10))
            )
            if filters:
                query = query.where(*filters)
            return [
                {"date": row[0], "value": int(row[1] or 0)}
                for row in session.exec(query).all()
            ]

        if metric == "errors":
            query = (
                select(
                    func.substr(ProviderCallLog.created_at, 1, 10).label("date"),
                    _error_count().label("value"),
                )
                .group_by(func.substr(ProviderCallLog.created_at, 1, 10))
                .order_by(func.substr(ProviderCallLog.created_at, 1, 10))
            )
            if filters:
                query = query.where(*filters)
            return [
                {"date": row[0], "value": int(row[1] or 0)}
                for row in session.exec(query).all()
            ]

        if metric == "api_calls":
            query = (
                select(
                    func.substr(ProviderCallLog.created_at, 1, 10).label("date"),
                    func.count(ProviderCallLog.id).label("value"),
                )
                .group_by(func.substr(ProviderCallLog.created_at, 1, 10))
                .order_by(func.substr(ProviderCallLog.created_at, 1, 10))
            )
            if filters:
                query = query.where(*filters)
            return [
                {"date": row[0], "value": int(row[1] or 0)}
                for row in session.exec(query).all()
            ]

        if metric == "avg_duration":
            query = (
                select(
                    func.substr(ProviderCallLog.created_at, 1, 10).label("date"),
                    func.coalesce(func.avg(ProviderCallLog.duration_ms), 0).label("value"),
                )
                .group_by(func.substr(ProviderCallLog.created_at, 1, 10))
                .order_by(func.substr(ProviderCallLog.created_at, 1, 10))
            )
            if filters:
                query = query.where(*filters)
            return [
                {"date": row[0], "value": round(float(row[1] or 0))}
                for row in session.exec(query).all()
            ]

        return []
