import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from pythonjsonlogger.json import JsonFormatter

from app.core.config import get_settings


class StructuredJsonFormatter(JsonFormatter):
    """JSON formatter with custom field mapping."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rename_fields = {
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        }

    def add_fields(self, log_data: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_data, record, message_dict)
        for old_name, new_name in self._rename_fields.items():
            if old_name in record.__dict__:
                log_data[new_name] = record.__dict__.pop(old_name)
        if "request_id" not in log_data:
            log_data["request_id"] = ""


def _build_formatter(fmt: str) -> logging.Formatter | StructuredJsonFormatter:
    if fmt == "json":
        return StructuredJsonFormatter(
            "%(timestamp)s %(level)s %(logger)s %(message)s"
        )
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
