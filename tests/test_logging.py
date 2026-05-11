import json
import logging
import os

import pytest

from app.core import logging as app_logging


def _make_settings(ld, lf="json"):
    """Build a fake settings object."""
    class FakeSettings:
        log_level = "INFO"
        log_format = lf
        log_dir = ld
        log_retention_days = 7
    return FakeSettings()


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging handlers before each test so setup_logging starts clean."""
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    root.setLevel(logging.WARNING)
    yield
    for h in list(root.handlers):
        root.removeHandler(h)
    root.setLevel(logging.WARNING)


def test_setup_logging_creates_log_dir(tmp_path, monkeypatch):
    """setup_logging 创建 log_dir 目录"""
    log_dir = str(tmp_path / "logs")
    monkeypatch.setattr("app.core.logging.get_settings", lambda: _make_settings(log_dir, lf="text"))
    app_logging.setup_logging()
    assert os.path.isdir(log_dir)


def test_json_format_output(tmp_path, monkeypatch, capsys):
    """LOG_FORMAT=json 时输出合法 JSON"""
    log_dir = str(tmp_path / "logs")
    monkeypatch.setattr("app.core.logging.get_settings", lambda: _make_settings(log_dir, lf="json"))
    app_logging.setup_logging()
    logger = app_logging.get_logger("test_json")
    logger.info("json_test_message")

    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().split("\n") if l.strip()]
    assert len(lines) >= 1
    parsed = json.loads(lines[-1])
    assert "timestamp" in parsed
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_json"
    assert parsed["message"] == "json_test_message"


def test_text_format_output(tmp_path, monkeypatch, capsys):
    """LOG_FORMAT=text 时输出可读文本"""
    log_dir = str(tmp_path / "logs")
    monkeypatch.setattr("app.core.logging.get_settings", lambda: _make_settings(log_dir, lf="text"))
    app_logging.setup_logging()
    logger = app_logging.get_logger("test_text")
    logger.info("text_test_message")

    captured = capsys.readouterr()
    output = captured.out
    assert "test_text" in output
    assert "text_test_message" in output


def test_extra_fields_in_json(tmp_path, monkeypatch, capsys):
    """extra 字段被合并到 JSON 输出"""
    log_dir = str(tmp_path / "logs")
    monkeypatch.setattr("app.core.logging.get_settings", lambda: _make_settings(log_dir, lf="json"))
    app_logging.setup_logging()
    logger = app_logging.get_logger("test_extra")
    logger.info("extra_test", extra={"job_id": "job_123", "provider": "minimax"})

    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().split("\n") if l.strip()]
    parsed = json.loads(lines[-1])
    assert parsed.get("job_id") == "job_123"
    assert parsed.get("provider") == "minimax"


def test_log_file_created(tmp_path, monkeypatch):
    """日志文件被创建"""
    log_dir = str(tmp_path / "logs")
    monkeypatch.setattr("app.core.logging.get_settings", lambda: _make_settings(log_dir, lf="text"))
    app_logging.setup_logging()
    logger = app_logging.get_logger("test_file")
    logger.info("file_test")

    log_file = os.path.join(log_dir, "voice_lab.log")
    assert os.path.isfile(log_file)


def test_get_logger_returns_named_logger(monkeypatch):
    """get_logger 返回正确命名的 logger"""
    monkeypatch.setattr("app.core.logging.get_settings", lambda: _make_settings("/tmp/fake", "text"))
    app_logging.setup_logging()
    logger = app_logging.get_logger("my_service")
    assert logger.name == "my_service"
    assert isinstance(logger, logging.Logger)


def test_backward_compatible_percent_format(tmp_path, monkeypatch, capsys):
    """% 占位符格式继续正常工作"""
    log_dir = str(tmp_path / "logs")
    monkeypatch.setattr("app.core.logging.get_settings", lambda: _make_settings(log_dir, lf="text"))
    app_logging.setup_logging()
    logger = app_logging.get_logger("test_fmt")
    logger.info("render_start job=%s provider=%s", "job_abc", "mock")

    captured = capsys.readouterr()
    assert "job_abc" in captured.out
    assert "mock" in captured.out


def test_backward_compatible_percent_format_json(tmp_path, monkeypatch, capsys):
    """% 占位符格式在 JSON 模式也正常"""
    log_dir = str(tmp_path / "logs")
    monkeypatch.setattr("app.core.logging.get_settings", lambda: _make_settings(log_dir, lf="json"))
    app_logging.setup_logging()
    logger = app_logging.get_logger("test_fmt_json")
    logger.info("render_failed job=%s error=%s", "job_xyz", "timeout_error")

    captured = capsys.readouterr()
    lines = [l for l in captured.out.strip().split("\n") if l.strip()]
    parsed = json.loads(lines[-1])
    assert "job_xyz" in parsed["message"]
    assert "timeout_error" in parsed["message"]
