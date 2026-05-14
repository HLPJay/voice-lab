"""Tests for /api/voice/jobs returning audio_asset fields."""
from fastapi.testclient import TestClient


def test_list_jobs_returns_audio_asset(test_app, seed_mock_binding):
    """GET /api/voice/jobs returns audio_asset for jobs with assets."""
    client = TestClient(test_app)

    # Create a render job which saves an audio asset
    render_resp = client.post(
        "/api/voice/render",
        json={
            "text": "历史音频资产字段测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert render_resp.status_code == 200
    render_data = render_resp.json()
    job_id = render_data["job_id"]
    audio_asset_id = render_data["audio_asset"]["id"]

    # List jobs and find our job
    jobs_resp = client.get("/api/voice/jobs?limit=10&offset=0")
    assert jobs_resp.status_code == 200
    jobs_data = jobs_resp.json()
    assert "jobs" in jobs_data
    assert "total" in jobs_data

    matched = next((j for j in jobs_data["jobs"] if j["job_id"] == job_id), None)
    assert matched is not None, f"job {job_id} not found in list response"
    assert matched["audio_asset"] is not None, "audio_asset should not be null for completed job"
    assert matched["audio_asset"]["id"] == audio_asset_id
    assert matched["audio_asset"]["url"] == f"/api/voice/assets/{audio_asset_id}/download"
    assert matched["audio_asset"]["duration_ms"] is not None
    assert matched["audio_asset"]["format"] is not None


def test_get_job_returns_audio_asset(test_app, seed_mock_binding):
    """GET /api/voice/jobs/{job_id} returns audio_asset for jobs with assets."""
    client = TestClient(test_app)

    # Create a render job
    render_resp = client.post(
        "/api/voice/render",
        json={
            "text": "历史详情音频资产字段测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert render_resp.status_code == 200
    render_data = render_resp.json()
    job_id = render_data["job_id"]
    audio_asset_id = render_data["audio_asset"]["id"]

    # Get single job
    job_resp = client.get(f"/api/voice/jobs/{job_id}")
    assert job_resp.status_code == 200
    job_data = job_resp.json()

    assert job_data["job_id"] == job_id
    assert job_data["audio_asset"] is not None
    assert job_data["audio_asset"]["id"] == audio_asset_id
    assert job_data["audio_asset"]["url"] == f"/api/voice/assets/{audio_asset_id}/download"
    assert job_data["audio_asset"]["duration_ms"] is not None


def test_job_without_audio_asset_returns_null_audio_asset(test_app, seed_mock_binding, session):
    """A job without an audio asset returns audio_asset: null."""
    from sqlmodel import Session
    from app.models.voice_job import VoiceJob
    from app.core.time import utc_now_iso

    # Create a job directly without going through render (no asset)
    now = utc_now_iso()
    job = VoiceJob(
        id="job_no_asset_test",
        job_type="sync_render",
        status="failed",
        provider="mock",
        model="speech-02-hd",
        input_text="测试无资产任务",
        error_message="mock failure for test",
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()

    client = TestClient(test_app)
    job_resp = client.get("/api/voice/jobs/job_no_asset_test")
    assert job_resp.status_code == 200
    job_data = job_resp.json()

    assert job_data["job_id"] == "job_no_asset_test"
    assert job_data["audio_asset"] is None
    assert job_data["subtitle_asset"] is None


def test_list_jobs_returns_null_audio_asset_for_jobs_without_assets(test_app, seed_mock_binding, session):
    """GET /api/voice/jobs returns audio_asset: null for jobs without assets."""
    from sqlmodel import Session
    from app.models.voice_job import VoiceJob
    from app.core.time import utc_now_iso

    # Create a job without asset
    now = utc_now_iso()
    job = VoiceJob(
        id="job_no_asset_list_test",
        job_type="sync_render",
        status="failed",
        provider="mock",
        model="speech-02-hd",
        input_text="测试无资产列表任务",
        error_message="mock failure",
        created_at=now,
        updated_at=now,
    )
    session.add(job)
    session.commit()

    client = TestClient(test_app)
    jobs_resp = client.get("/api/voice/jobs?limit=10&offset=0")
    assert jobs_resp.status_code == 200
    jobs_data = jobs_resp.json()

    matched = next((j for j in jobs_data["jobs"] if j["job_id"] == "job_no_asset_list_test"), None)
    assert matched is not None
    assert matched["audio_asset"] is None
