from fastapi.testclient import TestClient


def test_submit_async_task(test_app, seed_profile, seed_mock_binding):
    """POST /api/voice/render/async returns job_id with processing status."""
    resp = TestClient(test_app).post(
        "/api/voice/render/async",
        json={
            "text": "异步长文本语音生成测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"].startswith("job_")
    assert data["status"] == "processing"
    assert data["provider"] == "mock"
    assert data["model"]


def test_query_status_success(test_app, seed_profile, seed_mock_binding):
    """GET status after submit returns success with audio asset."""
    client = TestClient(test_app)
    submit = client.post(
        "/api/voice/render/async",
        json={
            "text": "异步状态查询测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert submit.status_code == 200
    job_id = submit.json()["job_id"]

    status = client.get(f"/api/voice/render/async/{job_id}/status")
    assert status.status_code == 200
    data = status.json()
    assert data["status"] == "success"
    assert data["audio_asset"] is not None
    assert data["audio_asset"]["id"].startswith("audio_")


def test_query_status_with_subtitle(test_app, seed_profile, seed_mock_binding):
    """Async render with need_subtitle=True produces subtitle asset on completion."""
    client = TestClient(test_app)
    submit = client.post(
        "/api/voice/render/async",
        json={
            "text": "异步字幕测试。",
            "provider": "mock",
            "need_subtitle": True,
        },
    )
    assert submit.status_code == 200
    job_id = submit.json()["job_id"]

    status = client.get(f"/api/voice/render/async/{job_id}/status")
    assert status.status_code == 200
    data = status.json()
    assert data["status"] == "success"
    assert data["subtitle_asset"] is not None
    assert data["subtitle_asset"]["id"].startswith("subtitle_")


def test_query_nonexistent_job(test_app, seed_profile):
    """Query a non-existent job_id returns 404."""
    resp = TestClient(test_app).get("/api/voice/render/async/job_nonexistent/status")
    assert resp.status_code == 404


def test_already_completed_job_returns_cached(test_app, seed_profile, seed_mock_binding):
    """Querying a completed job again returns same result without re-downloading."""
    client = TestClient(test_app)
    submit = client.post(
        "/api/voice/render/async",
        json={
            "text": "重复查询测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    job_id = submit.json()["job_id"]

    first = client.get(f"/api/voice/render/async/{job_id}/status")
    second = client.get(f"/api/voice/render/async/{job_id}/status")
    assert first.json()["status"] == "success"
    assert second.json()["status"] == "success"
    assert first.json()["audio_asset"]["id"] == second.json()["audio_asset"]["id"]


def test_submit_empty_text_rejected(test_app, seed_profile):
    """Empty text is rejected by request validation."""
    resp = TestClient(test_app).post(
        "/api/voice/render/async",
        json={
            "text": "",
            "provider": "mock",
        },
    )
    assert resp.status_code == 422
