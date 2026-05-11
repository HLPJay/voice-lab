import json
import logging
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.core import logging as app_logging


@pytest.fixture(autouse=True)
def _setup_json_logging():
    """Ensure JSON logging is active for all tests in this module."""
    class FakeSettings:
        log_level = "INFO"
        log_format = "json"
        log_dir = tempfile.mkdtemp()
        log_retention_days = 7

    import app.core.logging
    orig = app.core.logging.get_settings
    app.core.logging.get_settings = lambda: FakeSettings()

    root = logging.getLogger()
    orig_level = root.level
    orig_handlers = list(root.handlers)

    root.handlers.clear()
    root.setLevel(logging.INFO)
    app_logging.setup_logging()

    yield

    app.core.logging.get_settings = orig
    root.handlers.clear()
    for h in orig_handlers:
        root.addHandler(h)
    root.setLevel(orig_level)


def test_response_has_request_id_header(test_app):
    """Response 包含 X-Request-ID header"""
    client = TestClient(test_app)
    resp = client.get("/health")
    assert "X-Request-ID" in resp.headers
    assert resp.headers["X-Request-ID"].startswith("req_")


def test_request_id_format(test_app):
    """request_id 格式为 req_ + 12位hex"""
    client = TestClient(test_app)
    resp = client.get("/health")
    rid = resp.headers["X-Request-ID"]
    assert len(rid) == 16
    assert rid.startswith("req_")


def test_request_id_unique_per_request(test_app):
    """每个请求的 request_id 不同"""
    client = TestClient(test_app)
    r1 = client.get("/health")
    r2 = client.get("/health")
    assert r1.headers["X-Request-ID"] != r2.headers["X-Request-ID"]


def test_request_log_contains_request_id(test_app, caplog):
    """日志中包含 request_id"""
    caplog.set_level(logging.INFO)
    client = TestClient(test_app)
    client.post(
        "/api/voice/render",
        json={"text": "test", "provider": "mock"},
    )

    request_ids = [rec.request_id for rec in caplog.records if hasattr(rec, "request_id")]
    assert any(rid and rid.startswith("req_") for rid in request_ids)


def test_health_no_request_log(test_app, caplog):
    """GET /health 不产生 request_start/request_end 日志"""
    caplog.set_level(logging.INFO)
    client = TestClient(test_app)
    client.get("/health")

    messages = [rec.message for rec in caplog.records]
    assert "request_start" not in messages
    assert "request_end" not in messages