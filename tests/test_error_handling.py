import logging

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.core.errors import JobNotFound, VoiceLabError


def test_voice_lab_error_produces_warning_log(test_app, caplog):
    """VoiceLabError 触发 WARNING 日志"""
    caplog.set_level(logging.WARNING)
    client = TestClient(test_app)

    resp = client.get("/api/voice/jobs/nonexistent_job_id_for_testing")
    assert resp.status_code == 404

    records = caplog.records
    voice_lab_errors = [rec for rec in records if rec.message == "voice_lab_error"]
    assert len(voice_lab_errors) >= 1, f"Expected voice_lab_error in {[(r.message, r.levelname) for r in records]}"

    err = voice_lab_errors[0]
    assert err.levelno == logging.WARNING
    assert err.error_code == "JOB_NOT_FOUND"
    assert err.path == "/api/voice/jobs/nonexistent_job_id_for_testing"
    assert err.method == "GET"


def test_validation_error_produces_warning_log(test_app, caplog):
    """RequestValidationError 触发 WARNING 日志"""
    caplog.set_level(logging.WARNING)
    client = TestClient(test_app)

    resp = client.post("/api/voice/render", json={})
    assert resp.status_code == 422

    records = caplog.records
    validation_errors = [rec for rec in records if rec.message == "validation_error"]
    assert len(validation_errors) >= 1, f"Expected validation_error in {[(r.message, r.levelname) for r in records]}"

    err = validation_errors[0]
    assert err.levelno == logging.WARNING
    assert err.error_code == "VALIDATION_ERROR"
    assert err.path == "/api/voice/render"
    assert err.method == "POST"


def _make_crash_app():
    """Create a minimal FastAPI app with a crashing route for testing."""
    from app.core.errors import unhandled_error_handler
    from app.core.middleware import RequestContextMiddleware

    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(Exception, unhandled_error_handler)

    @app.get("/test/crash")
    async def crash():
        raise RuntimeError("intentional crash for testing")

    return app


def test_unhandled_error_returns_500_json():
    """未捕获异常返回统一 500 JSON 格式"""
    app = _make_crash_app()
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/test/crash")
    assert resp.status_code == 500

    body = resp.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"] == "Internal server error"
    assert body["error"]["detail"] is None
    assert body["error"]["job_id"] is None


def test_unhandled_error_produces_error_log(caplog):
    """未捕获异常触发 ERROR 日志"""
    app = _make_crash_app()
    client = TestClient(app, raise_server_exceptions=False)

    caplog.set_level(logging.ERROR, "error_handler")
    resp = client.get("/test/crash")
    assert resp.status_code == 500

    unhandled_errors = [rec for rec in caplog.records if rec.message == "unhandled_error"]
    assert len(unhandled_errors) >= 1

    err = unhandled_errors[0]
    assert err.levelno == logging.ERROR
    assert err.error_type == "RuntimeError"
    assert "intentional crash" in err.error_message


def test_unhandled_error_does_not_leak_internals():
    """500 响应不泄露内部堆栈"""
    app = _make_crash_app()
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.get("/test/crash")
    assert resp.status_code == 500

    body = resp.json()
    body_str = str(body)

    assert "intentional crash" not in body_str
    assert "RuntimeError" not in body_str
    assert ".py" not in body_str
    assert "traceback" not in body_str.lower()


def test_error_response_has_request_id(test_app):
    """错误响应也包含 X-Request-ID header"""
    client = TestClient(test_app)

    resp = client.get("/api/voice/jobs/nonexistent_job_id_for_testing")
    assert resp.status_code == 404
    assert "X-Request-ID" in resp.headers
    assert resp.headers["X-Request-ID"].startswith("req_")
