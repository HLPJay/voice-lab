import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models.provider_call_log import ProviderCallLog


@pytest.fixture
def seed_call_logs(temp_db):
    """插入测试审计记录"""
    engine, _ = temp_db
    with Session(engine) as session:
        logs = [
            ProviderCallLog(
                id="calllog_001",
                provider="minimax",
                api_path="/v1/t2a_v2",
                method="POST",
                status_code=200,
                duration_ms=1500,
                created_at="2026-05-11T10:00:00+00:00",
            ),
            ProviderCallLog(
                id="calllog_002",
                provider="minimax",
                api_path="/v1/get_voice",
                method="POST",
                status_code=200,
                duration_ms=600,
                request_id="req_aaa",
                job_id="job_001",
                created_at="2026-05-11T11:00:00+00:00",
            ),
            ProviderCallLog(
                id="calllog_003",
                provider="minimax",
                api_path="/v1/t2a_v2",
                method="POST",
                status_code=None,
                duration_ms=30000,
                error_type="TimeoutException",
                error_message="connection timeout",
                created_at="2026-05-11T12:00:00+00:00",
            ),
        ]
        for log in logs:
            session.add(log)
        session.commit()


def test_call_logs_list_all(test_app, seed_call_logs):
    """无过滤条件返回全部记录"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/call-logs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["logs"]) == 3


def test_call_logs_filter_by_provider(test_app, seed_call_logs):
    """按 provider 过滤"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/call-logs?provider=minimax")
    assert resp.json()["total"] == 3
    resp = client.get("/api/admin/call-logs?provider=openai")
    assert resp.json()["total"] == 0


def test_call_logs_filter_by_api_path(test_app, seed_call_logs):
    """按 api_path 过滤"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/call-logs?api_path=/v1/t2a_v2")
    assert resp.json()["total"] == 2
    resp = client.get("/api/admin/call-logs?api_path=/v1/get_voice")
    assert resp.json()["total"] == 1
    resp = client.get("/api/admin/call-logs?api_path=/v1/nonexistent")
    assert resp.json()["total"] == 0


def test_call_logs_filter_by_status(test_app, seed_call_logs):
    """按 status=success/error 过滤"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/call-logs?status=success")
    assert resp.json()["total"] == 2
    resp = client.get("/api/admin/call-logs?status=error")
    assert resp.json()["total"] == 1


def test_call_logs_filter_by_time_range(test_app, seed_call_logs):
    """按时间范围过滤"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/call-logs?start=2026-05-11T11:00:00+00:00")
    assert resp.json()["total"] == 2
    resp = client.get(
        "/api/admin/call-logs?start=2026-05-11T11:00:00+00:00&end=2026-05-11T12:00:00+00:00"
    )
    assert resp.json()["total"] == 1


def test_call_logs_pagination(test_app, seed_call_logs):
    """分页 limit/offset"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/call-logs?limit=1&offset=0")
    body = resp.json()
    assert len(body["logs"]) == 1
    assert body["total"] == 3
    assert body["logs"][0]["id"] == "calllog_003"

    resp = client.get("/api/admin/call-logs?limit=1&offset=1")
    body = resp.json()
    assert len(body["logs"]) == 1
    assert body["logs"][0]["id"] == "calllog_002"


def test_call_logs_order_desc(test_app, seed_call_logs):
    """按 created_at DESC 排序"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/call-logs")
    body = resp.json()
    ids = [log["id"] for log in body["logs"]]
    assert ids == ["calllog_003", "calllog_002", "calllog_001"]


def test_call_logs_limit_cap(test_app, seed_call_logs):
    """limit 超过 200 被钳制"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/call-logs?limit=999")
    assert resp.json()["limit"] == 200


def test_call_logs_filter_by_job_id(test_app, seed_call_logs):
    """按 job_id 过滤"""
    client = TestClient(test_app)
    resp = client.get("/api/admin/call-logs?job_id=job_001")
    assert resp.json()["total"] == 1
    assert resp.json()["logs"][0]["id"] == "calllog_002"
    resp = client.get("/api/admin/call-logs?job_id=nonexistent")
    assert resp.json()["total"] == 0
