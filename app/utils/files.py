from pathlib import Path

from app.core.config import get_settings
from app.core.time import date_path


def storage_path(kind: str, filename: str) -> Path:
    path = Path(get_settings().storage_dir) / kind / date_path()
    path.mkdir(parents=True, exist_ok=True)
    return path / filename


def ensure_storage_dirs() -> None:
    root = Path(get_settings().storage_dir)
    for child in ["audio", "subtitles", "metadata", "temp"]:
        (root / child).mkdir(parents=True, exist_ok=True)
