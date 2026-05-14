"""Tests for DELETE /api/voice/jobs/{job_id} soft delete."""
from fastapi.testclient import TestClient


def test_delete_job_hides_from_history_list(test_app, seed_mock_binding):
    """Deleting a job removes it from the default history list."""
    client = TestClient(test_app)

    render_resp = client.post(
        "/api/voice/render",
        json={
            "text": "历史删除测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert render_resp.status_code == 200
    job_id = render_resp.json()["job_id"]

    delete_resp = client.delete(f"/api/voice/jobs/{job_id}")
    assert delete_resp.status_code == 200
    data = delete_resp.json()
    assert data["job_id"] == job_id
    assert data["deleted"] is True
    assert data["status"] == "deleted"

    list_resp = client.get("/api/voice/jobs?limit=20&offset=0")
    assert list_resp.status_code == 200
    jobs = list_resp.json()["jobs"]
    assert all(job["job_id"] != job_id for job in jobs)


def test_get_deleted_job_returns_404(test_app, seed_mock_binding):
    """Getting a deleted job returns 404."""
    client = TestClient(test_app)

    render_resp = client.post(
        "/api/voice/render",
        json={
            "text": "历史删除详情测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert render_resp.status_code == 200
    job_id = render_resp.json()["job_id"]

    delete_resp = client.delete(f"/api/voice/jobs/{job_id}")
    assert delete_resp.status_code == 200

    get_resp = client.get(f"/api/voice/jobs/{job_id}")
    assert get_resp.status_code == 404


def test_delete_job_is_idempotent(test_app, seed_mock_binding):
    """Deleting an already-deleted job returns success (idempotent)."""
    client = TestClient(test_app)

    render_resp = client.post(
        "/api/voice/render",
        json={
            "text": "历史重复删除测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert render_resp.status_code == 200
    job_id = render_resp.json()["job_id"]

    first = client.delete(f"/api/voice/jobs/{job_id}")
    second = client.delete(f"/api/voice/jobs/{job_id}")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["deleted"] is True
    assert second.json()["status"] == "deleted"


def test_delete_missing_job_returns_404(test_app):
    """Deleting a non-existent job returns 404."""
    client = TestClient(test_app)

    resp = client.delete("/api/voice/jobs/job_not_exist")
    assert resp.status_code == 404


def test_list_deleted_jobs_when_status_deleted(test_app, seed_mock_binding):
    """GET /api/voice/jobs?status=deleted lists deleted jobs."""
    client = TestClient(test_app)

    render_resp = client.post(
        "/api/voice/render",
        json={
            "text": "历史删除筛选测试。",
            "provider": "mock",
            "need_subtitle": False,
        },
    )
    assert render_resp.status_code == 200
    job_id = render_resp.json()["job_id"]

    assert client.delete(f"/api/voice/jobs/{job_id}").status_code == 200

    resp = client.get("/api/voice/jobs?status=deleted&limit=20&offset=0")
    assert resp.status_code == 200
    jobs = resp.json()["jobs"]
    assert any(job["job_id"] == job_id for job in jobs)
