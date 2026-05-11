import time

import pytest
from fastapi.testclient import TestClient


def test_health_quick(test_app):
    """GET /health returns ok without any dependency checks."""
    client = TestClient(test_app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"] == "Voice Lab"


def test_health_detail_structure(test_app):
    """GET /health/detail returns complete structure."""
    client = TestClient(test_app)
    resp = client.get("/health/detail")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body
    assert "version" in body
    assert "uptime_seconds" in body
    assert "timestamp" in body
    assert "checks" in body
    checks = body["checks"]
    assert "database" in checks
    assert "storage" in checks
    assert "provider_minimax" in checks


def test_health_detail_database_check(test_app):
    """Database check returns healthy with latency."""
    client = TestClient(test_app)
    resp = client.get("/health/detail")
    assert resp.status_code == 200
    db = resp.json()["checks"]["database"]
    assert db["status"] == "healthy"
    assert isinstance(db["latency_ms"], (int, float))
    assert db["latency_ms"] >= 0


def test_health_detail_storage_check(test_app):
    """Storage check returns healthy, writable, with free space."""
    client = TestClient(test_app)
    resp = client.get("/health/detail")
    assert resp.status_code == 200
    storage = resp.json()["checks"]["storage"]
    assert storage["status"] == "healthy"
    assert storage["writable"] is True
    assert isinstance(storage["free_space_mb"], (int, float))
    assert storage["free_space_mb"] > 0


def test_health_detail_provider_no_data(test_app):
    """No provider call data returns status unknown."""
    client = TestClient(test_app)
    resp = client.get("/health/detail")
    assert resp.status_code == 200
    provider = resp.json()["checks"]["provider_minimax"]
    assert provider["status"] == "unknown"
    assert provider["total_calls_24h"] == 0
    assert provider["error_rate_24h"] == 0.0


def test_health_detail_overall_healthy(test_app):
    """All checks pass → overall status is healthy."""
    client = TestClient(test_app)
    resp = client.get("/health/detail")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"


def test_health_detail_uptime(test_app):
    """uptime_seconds is a positive number."""
    client = TestClient(test_app)
    resp = client.get("/health/detail")
    assert resp.status_code == 200
    assert isinstance(resp.json()["uptime_seconds"], (int, float))
    assert resp.json()["uptime_seconds"] >= 0
