import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.voice_asset import AudioAsset
from app.models.provider_call_log import ProviderCallLog
from app.models.voice_job import VoiceJob


@pytest.fixture
def seed_stats_data(temp_db):
    """插入统计测试数据：jobs + call_logs + audio_assets"""
    engine, _ = temp_db
    with Session(engine) as session:
        # 3 voice_jobs: 2 success, 1 failed
        jobs = [
            VoiceJob(
                id="job_001",
                job_type="render",
                status="success",
                provider="minimax",
                created_at="2026-05-10T10:00:00+00:00",
                updated_at="2026-05-10T10:00:00+00:00",
            ),
            VoiceJob(
                id="job_002",
                job_type="render",
                status="success",
                provider="minimax",
                created_at="2026-05-10T11:00:00+00:00",
                updated_at="2026-05-10T11:00:00+00:00",
            ),
            VoiceJob(
                id="job_003",
                job_type="render",
                status="failed",
                provider="minimax",
                created_at="2026-05-11T10:00:00+00:00",
                updated_at="2026-05-11T10:00:00+00:00",
            ),
        ]
        # 5 provider_call_logs: 4 success, 1 error, across 2 days
        call_logs = [
            ProviderCallLog(
                id="clog_001",
                provider="minimax",
                api_path="/v1/t2a_v2",
                method="POST",
                status_code=200,
                duration_ms=1500,
                usage_characters=100,
                created_at="2026-05-10T10:00:00+00:00",
            ),
            ProviderCallLog(
                id="clog_002",
                provider="minimax",
                api_path="/v1/t2a_v2",
                method="POST",
                status_code=200,
                duration_ms=2000,
                usage_characters=150,
                created_at="2026-05-10T11:00:00+00:00",
            ),
            ProviderCallLog(
                id="clog_003",
                provider="minimax",
                api_path="/v1/get_voice",
                method="POST",
                status_code=200,
                duration_ms=500,
                usage_characters=0,
                created_at="2026-05-10T11:30:00+00:00",
            ),
            ProviderCallLog(
                id="clog_004",
                provider="minimax",
                api_path="/v1/t2a_v2",
                method="POST",
                status_code=None,
                duration_ms=30000,
                error_type="TimeoutException",
                error_message="connection timeout",
                created_at="2026-05-11T10:00:00+00:00",
            ),
            ProviderCallLog(
                id="clog_005",
                provider="minimax",
                api_path="/v1/t2a_v2",
                method="POST",
                status_code=200,
                duration_ms=1200,
                usage_characters=80,
                created_at="2026-05-11T12:00:00+00:00",
            ),
        ]
        # 2 audio_assets linked to success jobs
        assets = [
            AudioAsset(
                id="audio_001",
                job_id="job_001",
                provider="minimax",
                file_path="/fake/path1.mp3",
                duration_ms=5000,
                usage_characters=100,
                created_at="2026-05-10T10:00:00+00:00",
            ),
            AudioAsset(
                id="audio_002",
                job_id="job_002",
                provider="minimax",
                file_path="/fake/path2.mp3",
                duration_ms=7000,
                usage_characters=150,
                created_at="2026-05-10T11:00:00+00:00",
            ),
        ]
        for j in jobs:
            session.add(j)
        for c in call_logs:
            session.add(c)
        for a in assets:
            session.add(a)
        session.commit()


def test_summary_overview(test_app, seed_stats_data):
    """总览数据正确"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overview"]["total_jobs"] == 3
    assert body["overview"]["success_jobs"] == 2
    assert body["overview"]["failed_jobs"] == 1
    assert body["overview"]["success_rate"] == round(2 / 3, 3)
    assert body["overview"]["total_characters"] == 330  # 100+150+0+80 from call_logs


def test_summary_by_provider(test_app, seed_stats_data):
    """按 provider 统计正确"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/summary")
    assert resp.status_code == 200
    body = resp.json()
    minimax = body["by_provider"]["minimax"]
    assert minimax["api_calls"] == 5
    assert minimax["error_count"] == 1
    assert minimax["error_rate"] == round(1 / 5, 3)
    assert minimax["characters_used"] == 330


def test_summary_by_api(test_app, seed_stats_data):
    """按 API path 统计正确"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["by_api"]["/v1/t2a_v2"]["calls"] == 4
    assert body["by_api"]["/v1/t2a_v2"]["errors"] == 1
    assert body["by_api"]["/v1/get_voice"]["calls"] == 1
    assert body["by_api"]["/v1/get_voice"]["errors"] == 0


def test_summary_by_day(test_app, seed_stats_data):
    """按天统计正确"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/summary")
    assert resp.status_code == 200
    body = resp.json()
    by_day = {d["date"]: d for d in body["by_day"]}
    assert "2026-05-10" in by_day
    assert "2026-05-11" in by_day
    assert by_day["2026-05-10"]["jobs"] == 2
    assert by_day["2026-05-11"]["jobs"] == 1
    assert by_day["2026-05-10"]["api_calls"] == 3
    assert by_day["2026-05-11"]["api_calls"] == 2
    assert by_day["2026-05-11"]["errors"] == 1


def test_summary_with_time_filter(test_app, seed_stats_data):
    """时间过滤生效"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/summary?start=2026-05-11")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overview"]["total_jobs"] == 1
    # call_logs filtered to >= 2026-05-11: clog_004 (no chars) + clog_005 (80 chars)
    assert body["overview"]["total_characters"] == 80


def test_summary_empty_data(test_app):
    """无数据时返回全零"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["overview"]["total_jobs"] == 0
    assert body["overview"]["success_rate"] == 0
    assert body["overview"]["total_characters"] == 0
    assert body["by_provider"] == {}
    assert body["by_api"] == {}
    assert body["by_day"] == []


def test_daily_trend_jobs(test_app, seed_stats_data):
    """每日趋势 metric=jobs"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/daily?metric=jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["metric"] == "jobs"
    data = {d["date"]: d["value"] for d in body["data"]}
    assert data["2026-05-10"] == 2
    assert data["2026-05-11"] == 1


def test_daily_trend_errors(test_app, seed_stats_data):
    """每日趋势 metric=errors"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/daily?metric=errors")
    assert resp.status_code == 200
    body = resp.json()
    data = {d["date"]: d["value"] for d in body["data"]}
    assert data["2026-05-11"] == 1
    assert data.get("2026-05-10", 0) == 0


def test_daily_trend_unknown_metric(test_app, seed_stats_data):
    """未知 metric 返回空数据"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/daily?metric=unknown")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []


def test_daily_trend_characters_uses_audio_asset_fallback(test_app, temp_db):
    """当 ProviderCallLog.usage_characters 为 0 时，使用 AudioAsset.usage_characters"""
    engine, _ = temp_db
    with Session(engine) as session:
        # Job with no call_log chars but audio_asset with chars
        job = VoiceJob(
            id="job_fb_001",
            job_type="render",
            status="success",
            provider="minimax",
            created_at="2026-05-12T10:00:00+00:00",
            updated_at="2026-05-12T10:00:00+00:00",
        )
        # No call_log for this job (or call_log with null usage_characters)
        asset = AudioAsset(
            id="audio_fb_001",
            job_id="job_fb_001",
            provider="minimax",
            file_path="/fake/fallback.mp3",
            duration_ms=3000,
            usage_characters=123,
            created_at="2026-05-12T10:00:00+00:00",
        )
        session.add(job)
        session.add(asset)
        session.commit()

    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/daily?metric=characters")
    assert resp.status_code == 200
    body = resp.json()
    data = {d["date"]: d["value"] for d in body["data"]}
    assert data.get("2026-05-12", 0) == 123


def test_daily_trend_characters_uses_max_not_sum(test_app, temp_db):
    """同一天 call_chars 和 asset_chars 相同时，取 max 而非 sum（避免重复计数）"""
    engine, _ = temp_db
    with Session(engine) as session:
        job = VoiceJob(
            id="job_max_001",
            job_type="render",
            status="success",
            provider="minimax",
            created_at="2026-05-13T10:00:00+00:00",
            updated_at="2026-05-13T10:00:00+00:00",
        )
        # call_log with 100 chars
        call_log = ProviderCallLog(
            id="clog_max_001",
            provider="minimax",
            api_path="/v1/t2a_v2",
            method="POST",
            status_code=200,
            duration_ms=1500,
            usage_characters=100,
            created_at="2026-05-13T10:00:00+00:00",
        )
        # audio_asset also with 100 chars
        asset = AudioAsset(
            id="audio_max_001",
            job_id="job_max_001",
            provider="minimax",
            file_path="/fake/max.mp3",
            duration_ms=3000,
            usage_characters=100,
            created_at="2026-05-13T10:00:00+00:00",
        )
        session.add(job)
        session.add(call_log)
        session.add(asset)
        session.commit()

    client = TestClient(test_app)
    resp = client.get("/api/admin/stats/daily?metric=characters")
    assert resp.status_code == 200
    body = resp.json()
    data = {d["date"]: d["value"] for d in body["data"]}
    # Should be 100 (max of 100 and 100), not 200 (sum)
    assert data.get("2026-05-13", 0) == 100
