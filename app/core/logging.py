import datetime
import logging
import os
import sys
import zoneinfo
from logging.handlers import TimedRotatingFileHandler

from pythonjsonlogger.json import JsonFormatter

from app.core.config import get_settings
from app.core.context import get_request_id


class StructuredJsonFormatter(JsonFormatter):
    """JSON formatter with custom field mapping for pythonjsonlogger 4.x."""

    def add_fields(self, log_data: dict, record: logging.LogRecord, message_dict: dict) -> None:
        # Pre-inject request_id before anything else
        if not log_data.get("request_id"):
            log_data["request_id"] = get_request_id()
        # Manually set the standard fields with our desired names
        # (bypassing pythonjsonlogger's required_fields mechanism which would
        # try record.__dict__.get('level') returning None for all of them)
        log_data["timestamp"] = datetime.datetime.fromtimestamp(
            record.created, tz=zoneinfo.ZoneInfo("UTC")
        ).isoformat()
        log_data["level"] = record.levelname
        log_data["logger"] = record.name
        log_data["message"] = record.getMessage()
        # Merge any extra fields passed via extra={...}
        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "levelname", "levelno", "lineno",
                "module", "msecs", "message", "msg", "name", "pathname",
                "process", "processName", "relativeCreated", "stack_info",
                "thread", "threadName", "request_id",
            ):
                continue
            log_data[key] = value


def _build_formatter(fmt: str) -> logging.Formatter | StructuredJsonFormatter:
    if fmt == "json":
        return StructuredJsonFormatter()
    return logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")


def setup_logging() -> None:
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_format = settings.log_format
    log_dir = settings.log_dir
    retention_days = settings.log_retention_days

    os.makedirs(log_dir, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.handlers:
        root_logger.handlers.clear()

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(_build_formatter(log_format))
    root_logger.addHandler(stdout_handler)

    log_file_path = os.path.join(log_dir, "voice_lab.log")
    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when="midnight",
        interval=1,
        backupCount=retention_days,
        encoding="utf-8",
    )
    file_handler.setFormatter(_build_formatter(log_format))
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
